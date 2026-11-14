/* -*- Mode:C++; c-file-style:"gnu"; indent-tabs-mode:nil; -*- */
/*
 * ecn-lan.cc — Tái hiện thí nghiệm LAN của Floyd 1994
 * "TCP and Explicit Congestion Notification", ACM CCR 1994.
 *
 * Mô tả kịch bản (Section 6, Hình 1 của bài):
 *   - 5 kết nối TCP bulk-data (gói 1000 byte, không giới hạn dữ liệu)
 *   - 10 kết nối TCP telnet-like (gói 40 byte, tốc độ thấp)
 *   - Tất cả đi qua MỘT liên kết nghẽn tại gateway
 *   - 3 cấu hình: (A) DropTail, (B) RED không ECN, (C) RED + ECN
 *   - Biến thiên: kích thước buffer (60..240 kB), cửa sổ TCP (8/64 kB)
 *
 * Khác biệt có chủ đích với bài gốc (được ghi trong báo cáo):
 *   - TCP NewReno hiện đại thay cho Reno 4.3 BSD
 *   - Timer ns-3 tinh vi (min RTO 1s) thay cho đồng hồ TCP thô 0.1/100 ms
 *   - Gateway packet-based (buffer đếm theo gói ~1 kB)
 *
 * Kết quả xuất ra CSV để vẽ biểu đồ so sánh với bài gốc.
 *
 * Usage:
 *   ./ns3 run "scratch/ecn-lan --config=ecn --bufferKb=120 --winKb=64 --seed=1"
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

NS_LOG_COMPONENT_DEFINE("EcnLan");

// ---------- Tham số kịch bản (mặc định theo bài báo) ----------
static uint32_t g_nBulk      = 5;    // 5 luồng bulk-data
static uint32_t g_nTelnet    = 10;   // 10 luồng telnet-like
static uint32_t g_bulkPort   = 5000; // cổng bulk 5000..5004
static uint32_t g_telnetPort = 6000; // cổng telnet 6000..6009

// Biến toàn cục dùng cho trace
static uint32_t g_qdrops = 0;   // gói bị queue disc loại (drop)
static uint32_t g_cemarks = 0;  // gói bị đánh dấu CE (mark)

// Trace: gói rơi tại queue disc — "Drop": (item,)
static void
HandleQDrop(Ptr<const QueueDiscItem> item)
{
  g_qdrops++;
}

// Trace: gói bị RED đánh dấu CE — "Mark": (item, reason)
static void
HandleQMark(Ptr<const QueueDiscItem> item, const char* reason)
{
  g_cemarks++;
}

// Đường cong one-way delay trung bình & cao nhất của telnet lấy từ
// FlowMonitor delayHistogram (đơn vị giây, bucket đều).
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

int
main(int argc, char *argv[])
{
  std::string config = "ecn";    // dt | red | ecn
  uint32_t bufferKb  = 120;      // 60, 120, 180, 240 (bài gốc)
  uint32_t winKb     = 64;       // 8 hoặc 64 kB
  double simTime     = 15.0;     // 15 giây như bài gốc
  uint64_t run       = 1;        // số lần chạy (RngRun)
  std::string csvFile = "";

  CommandLine cmd(__FILE__);
  cmd.AddValue("config", "dt | red | ecn", config);
  cmd.AddValue("bufferKb", "Kích thước buffer switch (kB)", bufferKb);
  cmd.AddValue("winKb", "Cửa sổ TCP tối đa (kB)", winKb);
  cmd.AddValue("simTime", "Thời gian mô phỏng (s)", simTime);
  cmd.AddValue("run", "RNG run number (lặp nhiều seed)", run);
  cmd.AddValue("csv", "File CSV xuất kết quả (append)", csvFile);
  cmd.Parse(argc, argv);

  RngSeedManager::SetSeed(12345);
  RngSeedManager::SetRun(run);

  // ---------------- TCP (Reno-style -> NewReno) ----------------
  // Gói dữ liệu 1000 byte như bài; giới hạn cửa sổ Snd/Rcv = winKb
  Config::SetDefault("ns3::TcpSocket::SegmentSize", UintegerValue(1000));
  Config::SetDefault("ns3::TcpSocket::SndBufSize", UintegerValue(winKb * 1024));
  Config::SetDefault("ns3::TcpSocket::RcvBufSize", UintegerValue(winKb * 1024));
  Config::SetDefault("ns3::TcpL4Protocol::SocketType", StringValue("ns3::TcpNewReno"));
  // Bật/tắt ECN ở đầu TCP (chỉ cấu hình ecn mới bật)
  Config::SetDefault("ns3::TcpSocketBase::UseEcn",
                     StringValue(config == "ecn" ? "On" : "Off"));

  // ---------------- Dạng mạng (Figure 1) ----------------
  // 15 sender (5 bulk + 10 telnet) --100Mbps/10us--> GWa --100Mbps/10us--> GWb --> 15 sink
  NodeContainer senders;
  senders.Create(g_nBulk + g_nTelnet);
  NodeContainer routers;
  routers.Create(2); // GWa (có hàng đợi nghẽn), GWb
  NodeContainer sinks;
  sinks.Create(g_nBulk + g_nTelnet);

  PointToPointHelper p2pAccess;
  p2pAccess.SetDeviceAttribute("DataRate", StringValue("100Mbps"));
  p2pAccess.SetChannelAttribute("Delay", StringValue("10us"));
  // Queue của netdevice để nhỏ — hàng đợi chính nằm ở queue disc (qdisc)
  p2pAccess.SetQueue("ns3::DropTailQueue", "MaxSize", QueueSizeValue(QueueSize("1p")));

  PointToPointHelper p2pBottleneck;
  p2pBottleneck.SetDeviceAttribute("DataRate", StringValue("100Mbps"));
  p2pBottleneck.SetChannelAttribute("Delay", StringValue("10us"));
  p2pBottleneck.SetQueue("ns3::DropTailQueue", "MaxSize", QueueSizeValue(QueueSize("1p")));

  InternetStackHelper internet;
  internet.Install(senders);
  internet.Install(routers);
  internet.Install(sinks);

  // Địa chỉ theo subnet riêng cho mỗi link
  Ipv4AddressHelper address;
  std::vector<NetDeviceContainer> accessDevs; // link sender -> GWa
  for (uint32_t i = 0; i < senders.GetN(); i++)
    {
      NodeContainer pair = NodeContainer(senders.Get(i), routers.Get(0));
      NetDeviceContainer d = p2pAccess.Install(pair);
      accessDevs.push_back(d);
      std::ostringstream os;
      os << "10.1." << (i + 1) << ".0";
      address.SetBase(os.str().c_str(), "255.255.255.0");
      address.Assign(d);
    }

  // Liên kết nghẽn GWa -> GWb
  NodeContainer bneck = NodeContainer(routers.Get(0), routers.Get(1));
  NetDeviceContainer bneckDevs = p2pBottleneck.Install(bneck);
  address.SetBase("10.2.0.0", "255.255.255.0");
  address.Assign(bneckDevs);

  // Link GWb -> sink; luu lai dia chi IP cua tung sink de apps ket noi toi
  std::vector<Ipv4Address> sinkAddr(sinks.GetN());
  for (uint32_t i = 0; i < sinks.GetN(); i++)
    {
      NodeContainer pair = NodeContainer(routers.Get(1), sinks.Get(i));
      NetDeviceContainer d = p2pAccess.Install(pair);
      std::ostringstream os;
      os << "10.3." << (i + 1) << ".0";
      address.SetBase(os.str().c_str(), "255.255.255.0");
      Ipv4InterfaceContainer ifc = address.Assign(d);
      sinkAddr[i] = ifc.GetAddress(1); // device 1 = sink (device 0 = GWb)
    }

  Ipv4GlobalRoutingHelper::PopulateRoutingTables();

  // ---------------- Hàng đợi tại gateway (nút cổ chai) ----------------
  // Buffer đếm theo GÓI: 1 gói ~ 1000B dữ liệu + header ≈ 1kB
  // (gateway packet-based — giống bài; buffer 60..240 kB ~ 60..240 gói)
  uint32_t bufPkts = bufferKb; // 1 kB/gói xấp xỉ
  TrafficControlHelper tchU;
  tchU.Uninstall(bneckDevs.Get(0)); // xóa qdisc mặc định (nếu có) trước
  TrafficControlHelper tch;
  QueueDiscContainer qdiscs;
  if (config == "dt")
    {
      tch.SetRootQueueDisc("ns3::FifoQueueDisc",
                           "MaxSize", QueueSizeValue(QueueSize(std::to_string(bufPkts) + "p")));
      qdiscs = tch.Install(bneckDevs.Get(0));
    }
  else
    {
      // RED: minTh = buffer/12, maxTh = 3*minTh (bài gốc)
      double minTh = bufPkts / 12.0;
      double maxTh = 3.0 * minTh;
      bool useEcn = (config == "ecn");
      tch.SetRootQueueDisc("ns3::RedQueueDisc",
                           "MinTh", DoubleValue(minTh),
                           "MaxTh", DoubleValue(maxTh),
                           "LInterm", DoubleValue(0.1), // xac suat bao hieu toi da (maxP)
                           "QW", DoubleValue(0.002),
                           "MeanPktSize", UintegerValue(1000),
                           "UseEcn", BooleanValue(useEcn),
                           "MaxSize", QueueSizeValue(QueueSize(std::to_string(bufPkts) + "p")));
      qdiscs = tch.Install(bneckDevs.Get(0));
    }

  // Trace: drops và CE marks tại queue disc
  qdiscs.Get(0)->TraceConnectWithoutContext("Drop", MakeCallback(&HandleQDrop));
  qdiscs.Get(0)->TraceConnectWithoutContext("Mark", MakeCallback(&HandleQMark));

  // ---------------- Ứng dụng ----------------
  ApplicationContainer sinksApp;
  // 5 sink bulk + 10 sink telnet: cổng phân biệt để phân loại dòng
  for (uint32_t i = 0; i < g_nBulk; i++)
    {
      PacketSinkHelper sink("ns3::TcpSocketFactory",
                            InetSocketAddress(Ipv4Address::GetAny(), g_bulkPort + i));
      ApplicationContainer a = sink.Install(sinks.Get(i));
      a.Start(Seconds(0.0));
      a.Stop(Seconds(simTime));
      sinksApp.Add(a);
    }
  for (uint32_t i = 0; i < g_nTelnet; i++)
    {
      PacketSinkHelper sink("ns3::TcpSocketFactory",
                            InetSocketAddress(Ipv4Address::GetAny(), g_telnetPort + i));
      ApplicationContainer a = sink.Install(sinks.Get(g_nBulk + i));
      a.Start(Seconds(0.0));
      a.Stop(Seconds(simTime));
      sinksApp.Add(a);
    }

  // 5 luồng bulk: gửi không giới hạn, 1000 byte/gói, start dàn trong 1s đầu
  for (uint32_t i = 0; i < g_nBulk; i++)
    {
      BulkSendHelper bulk("ns3::TcpSocketFactory",
                          InetSocketAddress(sinkAddr[i], g_bulkPort + i));
      bulk.SetAttribute("SendSize", UintegerValue(1000));
      bulk.SetAttribute("MaxBytes", UintegerValue(0));
      ApplicationContainer a = bulk.Install(senders.Get(i));
      a.Start(Seconds(0.1 + i * 0.2));
      a.Stop(Seconds(simTime));
    }

  // 10 luồng telnet-like: gói 40 byte, ~640 bps (~2 gói/s — như tcplib trong bài)
  for (uint32_t i = 0; i < g_nTelnet; i++)
    {
      OnOffHelper onoff("ns3::TcpSocketFactory",
                        InetSocketAddress(sinkAddr[g_nBulk + i], g_telnetPort + i));
      onoff.SetAttribute("PacketSize", UintegerValue(40));
      onoff.SetAttribute("DataRate", DataRateValue(DataRate("640bps")));
      onoff.SetAttribute("OnTime", StringValue("ns3::ConstantRandomVariable[Constant=1000]"));
      onoff.SetAttribute("OffTime", StringValue("ns3::ConstantRandomVariable[Constant=0]"));
      ApplicationContainer a = onoff.Install(senders.Get(g_nBulk + i));
      a.Start(Seconds(1.0 + i * 0.1));
      a.Stop(Seconds(simTime));
    }

  // ---------------- mô phỏng & thu thập ----------------
  FlowMonitorHelper fmonh;
  Ptr<FlowMonitor> monitor = fmonh.InstallAll();

  Simulator::Stop(Seconds(simTime));
  Simulator::Run();

  monitor->CheckForLostPackets();

  // Phân loại dòng theo cổng đích
  Ptr<Ipv4FlowClassifier> classifier =
      DynamicCast<Ipv4FlowClassifier>(fmonh.GetClassifier());

  double bulkTotalBps = 0.0;
  double bulkMinBps = -1.0;
  double telnetDelaySum = 0.0;
  double telnetDelayWorst = 0.0;
  uint32_t telnetFlows = 0;
  uint32_t bulkFlows = 0;
  uint64_t lostTotal = 0;

  std::map<FlowId, FlowMonitor::FlowStats> stats = monitor->GetFlowStats();
  for (auto it = stats.begin(); it != stats.end(); ++it)
    {
      Ipv4FlowClassifier::FiveTuple t = classifier->FindFlow(it->first);
      lostTotal += it->second.lostPackets;

      bool isBulk = false;
      for (uint32_t i = 0; i < g_nBulk; i++)
        {
          if (t.destinationPort == g_bulkPort + i)
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

  std::cout << "=== ecn-lan === "
            << "config=" << config
            << " bufferKb=" << bufferKb
            << " winKb=" << winKb
            << " run=" << run << "\n"
            << "Bulk throughput aggregate : " << bulkTotalBps / 1e6 << " Mbps ("
            << bulkFlows << " flows)\n"
            << "Smallest bulk throughput : " << bulkMinBps / 1e6 << " Mbps\n"
            << "Telnet avg one-way delay  : " << telnetAvgDelayMs << " ms\n"
            << "Telnet worst one-way delay: " << telnetDelayWorst * 1000.0 << " ms\n"
            << "Queue disc drops          : " << g_qdrops << "\n"
            << "CE marks                  : " << g_cemarks << "\n"
            << "Lost packets (FlowMon)    : " << lostTotal << "\n";

  if (!csvFile.empty())
    {
      std::ofstream out(csvFile, std::ios::app);
      if (out.good())
        {
          out << config << "," << bufferKb << "," << winKb << "," << run << ","
              << bulkTotalBps / 1e6 << "," << bulkMinBps / 1e6 << ","
              << telnetAvgDelayMs << "," << telnetDelayWorst * 1000.0 << ","
              << g_qdrops << "," << g_cemarks << "," << lostTotal << "\n";
        }
    }

  Simulator::Destroy();
  return 0;
}
