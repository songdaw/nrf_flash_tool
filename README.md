# nrf_flash_tool
An user friendly flash tool for Nodic NRF52 chip.

This tool consists of "pynrfjprog" and GUI written in python. So, it needs nrfjprogdll, JLinkARMDLL and J-link driver the same as "pynrfjprog". But it has an user friendly GUI, NRF52 chip's download, lock and recover can be done by just click some buttons. No need to remember command lines.
![image]()

### **How To Use**
1. Install use driver for J-link
2. Choose the firmware file (bin or hex format)
3. Optional, if bin file is chosen, input the address you want to download.
4. Click Connect 
5. Click Download
6. Optional, if need to lock the chip, click Lock, after that the chip can not access until Recover.

