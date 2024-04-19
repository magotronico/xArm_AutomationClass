
# Personal Coursework Practices on xArm Automation

## Overview

This repository is a personal collection of my coursework practices focusing on automation with the xArm. It is intended as a reference for my own learning and documentation purposes.

## Prerequisites

- **Python Version**: Ensure Python 3.11.8 is installed for compatibility.
- **Virtual Environment**: Utilization of a virtual environment (.venv) is recommended for managing dependencies.
- **PLC Firmware**: Ensure using firmware 4.0. We tried using 4.5 and there were issues fixed by downgrading the firmware.

## Installation of xArm Python SDK

To interact with the xArm, the xArm Python SDK is required. Follow these steps for setup:

1. **Clone the SDK**:
   ```
   git clone https://github.com/xArm-Developer/xArm-Python-SDK.git
   ```
2. **SDK Installation**:
   Navigate to the SDK's directory and install using the setup script:
   ```
   cd xArm-Python-SDK
   python setup.py install
   ```

## Network Configuration for the xArm

Ensure the network configuration is as follows to facilitate communication with the xArm:

- Robot IP: 192.168.1.208
- Gateway(/Preferred DNS): 192.168.1.1
- PC IP: 192.168.1.55
- Laptop Ethernet IP: 192.168.1.8
- PLC IP: 192.168.1.1
- HMI IP: 192.168.1.2
- Camera IP 192.168.1.130
- Subnet Mask: 255.255.255.0

## Usage

This repository includes various practice codes and examples that are part of my coursework. It serves as a hands-on approach to understanding and implementing automation tasks with the xArm.

## Note

This collection is tailored for personal use and learning. For official guidance and support regarding the xArm Python SDK, refer to the [xArm Developer GitHub repository](https://github.com/xArm-Developer/xArm-Python-SDK).
