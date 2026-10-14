#include <sstream>
#include "ns3/core-module.h"
#include "ns3/network-module.h"
#include "ns3/internet-module.h"
#include "ns3/point-to-point-module.h"
#include "ns3/applications-module.h"

#include <fstream>
#include <iostream>
#include <string>
#include <cstdint>
#include <iterator>

using namespace ns3;

NS_LOG_COMPONENT_DEFINE("GuiNetworkDemo");

static std::string g_outputFile;

// Receives the complete UDP payload at Node 2.
static void
ReceiveMessage(Ptr<Socket> socket)
{
    Ptr<Packet> packet;

    while ((packet = socket->Recv()))
    {
        uint32_t size = packet->GetSize();

        std::string message(size, '\0');

        if (size > 0)
        {
            packet->CopyData(
                reinterpret_cast<uint8_t*>(&message[0]),
                size
            );
        }

        std::cout << "Node 2 received: " << message << std::endl;

        // Write the exact payload, including spaces and punctuation.
        std::ofstream output(g_outputFile, std::ios::binary | std::ios::trunc);

        if (output.is_open())
        {
            output.write(message.data(),
                         static_cast<std::streamsize>(message.size()));
            output.close();
        }
        else
        {
            std::cerr << "ERROR: Could not write to "
                      << g_outputFile << std::endl;
        }
    }
}

int
main(int argc, char* argv[])
{
	std::string message = "Hello, how are you?";
	std::string outputFile = "received_message.txt";

	std::ifstream messageInput("message_to_send.txt", std::ios::binary);
	if (messageInput.is_open())
	{
	    message.assign(
	        std::istreambuf_iterator<char>(messageInput),
	        std::istreambuf_iterator<char>()
	    );
	    messageInput.close();
	}

CommandLine cmd(__FILE__);
cmd.AddValue("output", "File for the received message", outputFile);
cmd.Parse(argc, argv);
    g_outputFile = outputFile;

    std::cout << "\n=== NS-3 GUI NETWORK SIMULATION ===" << std::endl;
    std::cout << "Message to send: " << message << std::endl;

    // Create Node 1 (sender) and Node 2 (receiver).
    NodeContainer nodes;
    nodes.Create(2);

    // Point-to-point link between the two nodes.
    PointToPointHelper pointToPoint;
    pointToPoint.SetDeviceAttribute(
        "DataRate", StringValue("10Mbps"));
    pointToPoint.SetChannelAttribute(
        "Delay", StringValue("5ms"));

    NetDeviceContainer devices = pointToPoint.Install(nodes);

    // Install the Internet protocol stack.
    InternetStackHelper internet;
    internet.Install(nodes);

    // Assign IP addresses to both ends of the link.
    Ipv4AddressHelper address;
    address.SetBase("10.1.1.0", "255.255.255.0");

    Ipv4InterfaceContainer interfaces = address.Assign(devices);

    // Node 2: UDP receiver on port 9000.
    const uint16_t port = 9000;

    Ptr<Socket> receiverSocket = Socket::CreateSocket(
        nodes.Get(1), UdpSocketFactory::GetTypeId());

    InetSocketAddress localAddress(
        Ipv4Address::GetAny(), port);

    if (receiverSocket->Bind(localAddress) != 0)
    {
        std::cerr << "ERROR: Receiver socket bind failed."
                  << std::endl;
        return 1;
    }

    receiverSocket->SetRecvCallback(
        MakeCallback(&ReceiveMessage));

    // Node 1: UDP sender.
    Ptr<Socket> senderSocket = Socket::CreateSocket(
        nodes.Get(0), UdpSocketFactory::GetTypeId());

    InetSocketAddress destination(
        interfaces.GetAddress(1), port);

    if (senderSocket->Connect(destination) != 0)
    {
        std::cerr << "ERROR: Sender socket connection failed."
                  << std::endl;
        return 1;
    }

    // Send the complete message at simulation time 0.1 seconds.
    Simulator::Schedule(
        Seconds(0.1),
        [senderSocket, message]()
        {
            Ptr<Packet> packet = Create<Packet>(
                reinterpret_cast<const uint8_t*>(message.data()),
                static_cast<uint32_t>(message.size())
            );

            int sent = senderSocket->Send(packet);

            if (sent >= 0)
            {
                std::cout << "Node 1 sent: " << message << std::endl;
            }
            else
            {
                std::cerr << "ERROR: UDP send failed." << std::endl;
            }
        }
    );

    // Allow sufficient time for delivery and reception.
    Simulator::Stop(Seconds(1.0));
    Simulator::Run();

    senderSocket->Close();
    receiverSocket->Close();

    Simulator::Destroy();

    std::cout << "=== SIMULATION FINISHED ===" << std::endl;

    return 0;
}
