/* -*- Mode:C++; c-file-style:"gnu"; indent-tabs-mode:nil; -*- */
/*
 * ecn-wan.cc — Tái hiện kịch bản WAN của Floyd 1994 (Section 7, Hình 4)
 *
 * Mô hình đơn giản hóa của Hình 4 (được ghi rõ trong báo cáo):
 *   Hai router A - B nối qua liên kết 45 Mbps / 10 ms (nút cổ chai),
 *   hai đầu có access link 100 Mbps / 2 ms (RTT ≈ 28-34 ms, xấp xỉ
 *   khoảng 21-40 ms trong bài). Lưu lượng hai chiều:
 *     - 4 luồng bulk/chiều (mức tải "vừa" như Hình 5)
 *     - 8 luồng telnet-like/chiều (gói 40 byte, 640 bps)
 *   So sánh 3 cấu hình: DropTail / RED / RED+ECN, cửa sổ TCP 64 kB.
 *   Thời gian chạy 10 giây như bài gốc.
 *
 * Usage:
 *   ./ns3 run "scratch/ecn-wan --config=ecn --seed=1"
 */

#include "ns3/core-module.h"
#include "ns3/network-module.h"
#include "ns3/internet-module.h"
#include "ns3/point-to-point-module.h"
#include "ns3/applications-module.h"
#include "ns3/traffic-control-module.h"
#include "ns3/flow-monitor-module.h"

#include <fstream>
#include <iostream>
#include <sstream>
#include <vector>

using namespace ns3;

NS_LOG_COMPONENT_DEFINE("EcnWan");

static uint32_t g_nBulk   = 4;  // bulk mỗi chiều (mức tải vừa)
static uint32_t g_nTelnet = 8;  // telnet-like mỗi chiều
static uint32_t g_bulkPortL = 5000;
static uint32_t g_telnetPortL = 6000;
static uint32_t g_bulkPortR = 7000;
static uint32_t g_telnetPortR = 8000;

static uint32_t g_qdropsA = 0;
static uint32_t g_qdropsB = 0;
static uint32_t g_cemarksA = 0;
static uint32_t g_cemarksB = 0;

static void
HandleQDropA(Ptr<const QueueDiscItem> item) { g_qdropsA++; }
static void
HandleQDropB(Ptr<const QueueDiscItem> item) { g_qdropsB++; }

static void
HandleQMarkA(Ptr<const QueueDiscItem> item, const char* reason) { g_cemarksA++; }
static void
HandleQMarkB(Ptr<const QueueDiscItem> item, const char* reason) { g_cemarksB++; }

static void
TelnetDelayFromHistogram(const Histogram &h, double &avg, double &worst)
{
  double sum = 0.0;
  uint32_t cnt = 0;
  worst = 0.0;
  for (uint32_t i = 0; i < h.GetNBins(); i++)
    {
      uint32_t c = h.GetBinCount(i);
      if (c == 0)
        {
          continue;
        }
      double mid = (h.GetBinStart(i) + h.GetBinEnd(i)) / 2.0;
      sum += mid * c;
      cnt += c;
      worst = h.GetBinEnd(i);
    }
  avg = (cnt > 0) ? (sum / cnt) : 0.0;
}

// Cài queue disc cho một device egress theo cấu hình
static Ptr<QueueDisc>
InstallQueueDisc(NetDeviceContainer &devs, uint32_t idx, const std::string &config,
                 uint32_t bufPkts, Ptr<QueueDisc> *outPtr)
{
  TrafficControlHelper tchU;
  tchU.Uninstall(devs.Get(idx)); // xóa qdisc mặc định (nếu có) trước
  TrafficControlHelper tch;
  QueueDiscContainer c;
  if (config == "dt")
    {
      tch.SetRootQueueDisc("ns3::FifoQueueDisc",
                           "MaxSize", QueueSizeValue(QueueSize(std::to_string(bufPkts) + "p")));
      c = tch.Install(devs.Get(idx));
    }
  else
    {
      double minTh = bufPkts / 12.0;
      double maxTh = 3.0 * minTh;
      bool useEcn = (config == "ecn");
      tch.SetRootQueueDisc("ns3::RedQueueDisc",
                           "MinTh", DoubleValue(minTh),
                           "MaxTh", DoubleValue(maxTh),
                           "LInterm", DoubleValue(0.1), // xac suat bao hieu toi da (maxP)
                           "QW", DoubleValue(0.001), // WAN: weight nhỏ hơn (bài gốc)
                           "MeanPktSize", UintegerValue(1000),
                           "UseEcn", BooleanValue(useEcn),
                           "MaxSize", QueueSizeValue(QueueSize(std::to_string(bufPkts) + "p")));
      c = tch.Install(devs.Get(idx));
    }
  *outPtr = c.Get(0);
  return c.Get(0);
}

int
main(int argc, char *argv[])
{
  std::string config = "ecn";
  uint32_t bufferKb  = 120;
  uint32_t winKb     = 64;
  double simTime     = 10.0;
  uint64_t run       = 1;
  std::string csvFile = "";

  CommandLine cmd(__FILE__);
  cmd.AddValue("config", "dt | red | ecn", config);
  cmd.AddValue("bufferKb", "Buffer (kB ~ gói)", bufferKb);
  cmd.AddValue("winKb", "Cửa sổ TCP (kB)", winKb);
  cmd.AddValue("simTime", "Giây mô phỏng", simTime);
  cmd.AddValue("run", "RNG run", run);
  cmd.AddValue("csv", "File CSV (append)", csvFile);
  cmd.Parse(argc, argv);

  RngSeedManager::SetSeed(12345);
  RngSeedManager::SetRun(run);

  Config::SetDefault("ns3::TcpSocket::SegmentSize", UintegerValue(1000));
  Config::SetDefault("ns3::TcpSocket::SndBufSize", UintegerValue(winKb * 1024));
  Config::SetDefault("ns3::TcpSocket::RcvBufSize", UintegerValue(winKb * 1024));
  Config::SetDefault("ns3::TcpL4Protocol::SocketType", StringValue("ns3::TcpNewReno"));
  Config::SetDefault("ns3::TcpSocketBase::UseEcn",
                     StringValue(config == "ecn" ? "On" : "Off"));

  // ------------- Topology: hostsL - GWa - GWb - hostsR -------------
  NodeContainer hostsL, hostsR, routers;
  hostsL.Create(2 * g_nBulk + 2 * g_nTelnet); // chiều L->R và R->L dùng chung pool node
  hostsR.Create(2 * g_nBulk + 2 * g_nTelnet);
  routers.Create(2);

  PointToPointHelper access;
  access.SetDeviceAttribute("DataRate", StringValue("100Mbps"));
  access.SetChannelAttribute("Delay", StringValue("2ms"));
  access.SetQueue("ns3::DropTailQueue", "MaxSize", QueueSizeValue(QueueSize("1p")));

  PointToPointHelper bottleneck;
  bottleneck.SetDeviceAttribute("DataRate", StringValue("45Mbps"));
  bottleneck.SetChannelAttribute("Delay", StringValue("10ms"));
  bottleneck.SetQueue("ns3::DropTailQueue", "MaxSize", QueueSizeValue(QueueSize("1p")));

  InternetStackHelper internet;
  internet.Install(hostsL);
  internet.Install(hostsR);
  internet.Install(routers);

  Ipv4AddressHelper address;
  uint32_t subnet = 1;
  std::vector<Ipv4Address> addrsL(hostsL.GetN()), addrsR(hostsR.GetN());
  for (uint32_t i = 0; i < hostsL.GetN(); i++)
    {
      NodeContainer pair = NodeContainer(hostsL.Get(i), routers.Get(0));
      NetDeviceContainer d = access.Install(pair);
      std::ostringstream os;
      os << "10.1." << subnet++ << ".0";
      address.SetBase(os.str().c_str(), "255.255.255.0");
      Ipv4InterfaceContainer ifc = address.Assign(d);
      addrsL[i] = ifc.GetAddress(0); // device 0 = host
    }
  for (uint32_t i = 0; i < hostsR.GetN(); i++)
    {
      NodeContainer pair = NodeContainer(hostsR.Get(i), routers.Get(1));
      NetDeviceContainer d = access.Install(pair);
      std::ostringstream os;
      os << "10.2." << subnet++ << ".0";
      address.SetBase(os.str().c_str(), "255.255.255.0");
      Ipv4InterfaceContainer ifc = address.Assign(d);
      addrsR[i] = ifc.GetAddress(0);
    }

  // Bottleneck GWa <-> GWb (45 Mbps, 10 ms)
  NodeContainer bneck = NodeContainer(routers.Get(0), routers.Get(1));
  NetDeviceContainer bneckDevs = bottleneck.Install(bneck);
  address.SetBase("10.9.0.0", "255.255.255.0");
  Ipv4InterfaceContainer bneckIf = address.Assign(bneckDevs);

  Ipv4GlobalRoutingHelper::PopulateRoutingTables();

  // Queue disc tại CẢ HAI egress của bottleneck (hai chiều)
  uint32_t bufPkts = bufferKb;
  Ptr<QueueDisc> qA, qB;
  InstallQueueDisc(bneckDevs, 0, config, bufPkts, &qA);
  InstallQueueDisc(bneckDevs, 1, config, bufPkts, &qB);
  qA->TraceConnectWithoutContext("Drop", MakeCallback(&HandleQDropA));
  qA->TraceConnectWithoutContext("Mark", MakeCallback(&HandleQMarkA));
  qB->TraceConnectWithoutContext("Drop", MakeCallback(&HandleQDropB));
  qB->TraceConnectWithoutContext("Mark", MakeCallback(&HandleQMarkB));

  // ------------- Apps -------------
  // L -> R: bulk (cổng 5000..), telnet (cổng 6000..)
  for (uint32_t i = 0; i < g_nBulk; i++)
    {
      PacketSinkHelper sink("ns3::TcpSocketFactory",
                            InetSocketAddress(Ipv4Address::GetAny(), g_bulkPortL + i));
      ApplicationContainer a = sink.Install(hostsR.Get(i));
      a.Start(Seconds(0.0));
      a.Stop(Seconds(simTime));

      BulkSendHelper bulk("ns3::TcpSocketFactory",
                          InetSocketAddress(addrsR[i], g_bulkPortL + i));
      bulk.SetAttribute("SendSize", UintegerValue(1000));
      ApplicationContainer s = bulk.Install(hostsL.Get(i));
      s.Start(Seconds(0.1 + i * 0.3));
      s.Stop(Seconds(simTime));
    }
  for (uint32_t i = 0; i < g_nTelnet; i++)
    {
      PacketSinkHelper sink("ns3::TcpSocketFactory",
                            InetSocketAddress(Ipv4Address::GetAny(), g_telnetPortL + i));
      ApplicationContainer a = sink.Install(hostsR.Get(g_nBulk + i));
      a.Start(Seconds(0.0));
      a.Stop(Seconds(simTime));

      OnOffHelper onoff("ns3::TcpSocketFactory",
                        InetSocketAddress(addrsR[g_nBulk + i], g_telnetPortL + i));
      onoff.SetAttribute("PacketSize", UintegerValue(40));
      onoff.SetAttribute("DataRate", DataRateValue(DataRate("640bps")));
      onoff.SetAttribute("OnTime", StringValue("ns3::ConstantRandomVariable[Constant=1000]"));
      onoff.SetAttribute("OffTime", StringValue("ns3::ConstantRandomVariable[Constant=0]"));
      ApplicationContainer s = onoff.Install(hostsL.Get(g_nBulk + i));
      s.Start(Seconds(1.0 + i * 0.1));
      s.Stop(Seconds(simTime));
    }

  // R -> L (lưu lượng hai chiều)
  for (uint32_t i = 0; i < g_nBulk; i++)
    {
      uint32_t src = hostsR.GetN() - (g_nBulk + g_nTelnet) + i;
      uint32_t dst = hostsL.GetN() - (g_nBulk + g_nTelnet) + i;
      PacketSinkHelper sink("ns3::TcpSocketFactory",
                            InetSocketAddress(Ipv4Address::GetAny(), g_bulkPortR + i));
      ApplicationContainer a = sink.Install(hostsL.Get(dst));
      a.Start(Seconds(0.0));
      a.Stop(Seconds(simTime));

      BulkSendHelper bulk("ns3::TcpSocketFactory",
                          InetSocketAddress(addrsL[dst], g_bulkPortR + i));
      bulk.SetAttribute("SendSize", UintegerValue(1000));
      ApplicationContainer s = bulk.Install(hostsR.Get(src));
      s.Start(Seconds(0.2 + i * 0.3));
      s.Stop(Seconds(simTime));
    }
  for (uint32_t i = 0; i < g_nTelnet; i++)
    {
      uint32_t src = hostsR.GetN() - g_nTelnet + i;
      uint32_t dst = hostsL.GetN() - g_nTelnet + i;
      PacketSinkHelper sink("ns3::TcpSocketFactory",
                            InetSocketAddress(Ipv4Address::GetAny(), g_telnetPortR + i));
      ApplicationContainer a = sink.Install(hostsL.Get(dst));
      a.Start(Seconds(0.0));
      a.Stop(Seconds(simTime));

      OnOffHelper onoff("ns3::TcpSocketFactory",
                        InetSocketAddress(addrsL[dst], g_telnetPortR + i));
      onoff.SetAttribute("PacketSize", UintegerValue(40));
      onoff.SetAttribute("DataRate", DataRateValue(DataRate("640bps")));
      onoff.SetAttribute("OnTime", StringValue("ns3::ConstantRandomVariable[Constant=1000]"));
      onoff.SetAttribute("OffTime", StringValue("ns3::ConstantRandomVariable[Constant=0]"));
      ApplicationContainer s = onoff.Install(hostsR.Get(src));
      s.Start(Seconds(1.0 + i * 0.1));
      s.Stop(Seconds(simTime));
    }

  FlowMonitorHelper fmonh;
  Ptr<FlowMonitor> monitor = fmonh.InstallAll();

  Simulator::Stop(Seconds(simTime));
  Simulator::Run();
  monitor->CheckForLostPackets();

  Ptr<Ipv4FlowClassifier> classifier =
      DynamicCast<Ipv4FlowClassifier>(fmonh.GetClassifier());

  double bulkTotalBps = 0.0, bulkMinBps = -1.0;
  double telnetDelaySum = 0.0, telnetDelayWorst = 0.0;
  uint32_t telnetFlows = 0, bulkFlows = 0;
  uint64_t lostTotal = 0;

  for (auto it = monitor->GetFlowStats().begin(); it != monitor->GetFlowStats().end(); ++it)
    {
      Ipv4FlowClassifier::FiveTuple t = classifier->FindFlow(it->first);
      lostTotal += it->second.lostPackets;

      bool isBulk = false;
      for (uint32_t i = 0; i < g_nBulk; i++)
        {
          if (t.destinationPort == g_bulkPortL + i || t.destinationPort == g_bulkPortR + i)
            {
              isBulk = true;
            }
        }
      double bps = (it->second.rxBytes * 8.0) / simTime;
      if (isBulk)
        {
          bulkTotalBps += bps;
          bulkFlows++;
          if (bulkMinBps < 0 || bps < bulkMinBps)
            {
              bulkMinBps = bps;
            }
        }
      else
        {
          double avg, worst;
          TelnetDelayFromHistogram(it->second.delayHistogram, avg, worst);
          if (avg > 0)
            {
              telnetDelaySum += avg;
              telnetDelayWorst = std::max(telnetDelayWorst, worst);
              telnetFlows++;
            }
        }
    }

  double telnetAvgDelayMs = (telnetFlows > 0) ? (telnetDelaySum / telnetFlows * 1000.0) : -1.0;
  uint32_t drops = g_qdropsA + g_qdropsB;
  uint32_t marks = g_cemarksA + g_cemarksB;

  std::cout << "=== ecn-wan === "
            << "config=" << config
            << " bufferKb=" << bufferKb
            << " winKb=" << winKb
            << " run=" << run << "\n"
            << "Bulk throughput aggregate : " << bulkTotalBps / 1e6 << " Mbps ("
            << bulkFlows << " flows)\n"
            << "Smallest bulk throughput : " << bulkMinBps / 1e6 << " Mbps\n"
            << "Telnet avg one-way delay  : " << telnetAvgDelayMs << " ms\n"
            << "Telnet worst one-way delay: " << telnetDelayWorst * 1000.0 << " ms\n"
            << "Queue disc drops (A+B)    : " << drops << "\n"
            << "CE marks (A+B)            : " << marks << "\n"
            << "Lost packets (FlowMon)    : " << lostTotal << "\n";

  if (!csvFile.empty())
    {
      std::ofstream out(csvFile, std::ios::app);
      if (out.good())
        {
          out << config << "," << bufferKb << "," << winKb << "," << run << ","
              << bulkTotalBps / 1e6 << "," << bulkMinBps / 1e6 << ","
              << telnetAvgDelayMs << "," << telnetDelayWorst * 1000.0 << ","
              << drops << "," << marks << "," << lostTotal << "\n";
        }
    }

  Simulator::Destroy();
  return 0;
}
