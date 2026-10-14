# NS-3 GUI Network Simulation

A Python Tkinter GUI connected to a C++ NS-3 network simulation.

## Architecture

UI 1 (Sender) -> NS-3 Node 1 -> Network Link -> NS-3 Node 2 -> UI 2 (Receiver)

## Files

- `gui_app.py` - Python sender and receiver windows.
- `scratch/gui-network.cc` - C++ NS-3 simulation.

## Requirements

- Ubuntu / WSL2 Ubuntu
- Python 3 with Tkinter
- Compatible NS-3 installation

## Setup

Copy `gui_app.py` to the root of your NS-3 project.
Copy `scratch/gui-network.cc` to its `scratch/` directory.

Build with:

    ./ns3 build

Launch with:

    python3 gui_app.py

Note: The current simulation uses a point-to-point link, not an actual mmWave radio model.
