from ctypes import *
from ctypes.wintypes import *
from sys import exit


def customresize(array, new_size):
    return (array._type_*new_size).from_address(addressof(array))

wlanapi = windll.LoadLibrary('wlanapi.dll')

ERROR_SUCCESS = 0

class GUID(Structure):
    _fields_ = [
        ('Data1', c_ulong),
        ('Data2', c_ushort),
        ('Data3', c_ushort),
        ('Data4', c_ubyte*8),
        ]

WLAN_INTERFACE_STATE = c_uint
(wlan_interface_state_not_ready,
 wlan_interface_state_connected,
 wlan_interface_state_ad_hoc_network_formed,
 wlan_interface_state_disconnecting,
 wlan_interface_state_disconnected,
 wlan_interface_state_associating,
 wlan_interface_state_discovering,
 wlan_interface_state_authenticating) = map(WLAN_INTERFACE_STATE, range(0, 8))

class WLAN_INTERFACE_INFO(Structure):
    _fields_ = [
        ("InterfaceGuid", GUID),
        ("strInterfaceDescription", c_wchar * 256),
        ("isState", WLAN_INTERFACE_STATE)
        ]

class WLAN_INTERFACE_INFO_LIST(Structure):
    _fields_ = [
        ("NumberOfItems", DWORD),
        ("Index", DWORD),
        ("InterfaceInfo", WLAN_INTERFACE_INFO * 1)
        ]

WLAN_MAX_PHY_TYPE_NUMBER = 0x8
DOT11_SSID_MAX_LENGTH = 32
WLAN_REASON_CODE = DWORD
DOT11_BSS_TYPE = c_uint
(dot11_BSS_type_infrastructure,
 dot11_BSS_type_independent,
 dot11_BSS_type_any) = map(DOT11_BSS_TYPE, range(1, 4))
DOT11_PHY_TYPE = c_uint
dot11_phy_type_unknown      = 0
dot11_phy_type_any          = 0
dot11_phy_type_fhss         = 1
dot11_phy_type_dsss         = 2
dot11_phy_type_irbaseband   = 3
dot11_phy_type_ofdm         = 4
dot11_phy_type_hrdsss       = 5
dot11_phy_type_erp          = 6
dot11_phy_type_ht           = 7
dot11_phy_type_IHV_start    = 0x80000000
dot11_phy_type_IHV_end      = 0xffffffff 

WLAN_AVAILABLE_NETWORK_CONNECTED = 1
WLAN_AVAILABLE_NETWORK_HAS_PROFILE = 2



class DOT11_SSID(Structure):
    _fields_ = [
        ("SSIDLength", c_ulong),
        ("SSID", c_char * DOT11_SSID_MAX_LENGTH)
        ]

class WLAN_AVAILABLE_NETWORK(Structure):
    _fields_ = [
        ("ProfileName", c_wchar * 256),
        ("dot11Ssid", DOT11_SSID),
        ("dot11BssType", DOT11_BSS_TYPE),
        ("NumberOfBssids", c_ulong),
        ("NetworkConnectable", c_bool),
        ("wlanNotConnectableReason", WLAN_REASON_CODE),
        ("NumberOfPhyTypes", c_ulong),
        ("dot11PhyTypes", DOT11_PHY_TYPE * WLAN_MAX_PHY_TYPE_NUMBER),
        ("MorePhyTypes", c_bool),
        ("wlanSignalQuality", c_ulong),
        ("SecurityEnabled", c_bool),
        ("Flags", DWORD),
        ("Reserved", DWORD)
        ]

class WLAN_AVAILABLE_NETWORK_LIST(Structure):
    _fields_ = [
        ("NumberOfItems", DWORD),
        ("Index", DWORD),
        ("Network", WLAN_AVAILABLE_NETWORK * 1)
        ]

WlanOpenHandle = wlanapi.WlanOpenHandle
WlanOpenHandle.argtypes = (DWORD, c_void_p, POINTER(DWORD), POINTER(HANDLE))
WlanOpenHandle.restype = DWORD

WlanEnumInterfaces = wlanapi.WlanEnumInterfaces
WlanEnumInterfaces.argtypes = (HANDLE, c_void_p, 
                               POINTER(POINTER(WLAN_INTERFACE_INFO_LIST)))
WlanEnumInterfaces.restype = DWORD

WlanGetAvailableNetworkList = wlanapi.WlanGetAvailableNetworkList
WlanGetAvailableNetworkList.argtypes = (HANDLE, POINTER(GUID), DWORD, c_void_p, 
                                        POINTER(POINTER(WLAN_AVAILABLE_NETWORK_LIST)))
WlanGetAvailableNetworkList.restype = DWORD

WlanFreeMemory = wlanapi.WlanFreeMemory
WlanFreeMemory.argtypes = [c_void_p]


if __name__ == '__main__':
    NegotiatedVersion = DWORD()
    ClientHandle = HANDLE()
    ret = WlanOpenHandle(1, None, byref(NegotiatedVersion), byref(ClientHandle))
    if ret != ERROR_SUCCESS:
        exit(FormatError(ret))

    # find all wireless network interfaces
    pInterfaceList = pointer(WLAN_INTERFACE_INFO_LIST())
    ret = WlanEnumInterfaces(ClientHandle, None, byref(pInterfaceList))
    if ret != ERROR_SUCCESS:
        exit(FormatError(ret))

    try:
        ifaces = customresize(pInterfaceList.contents.InterfaceInfo,
                              pInterfaceList.contents.NumberOfItems)
        # find each available network for each interface
        for iface in ifaces:
            print("Interface: {}".format(iface.strInterfaceDescription))
            pAvailableNetworkList = pointer(WLAN_AVAILABLE_NETWORK_LIST())
            ret = WlanGetAvailableNetworkList(ClientHandle, 
                                        byref(iface.InterfaceGuid),
                                        0,
                                        None,
                                        byref(pAvailableNetworkList))
            if ret != ERROR_SUCCESS:
                exit(FormatError(ret))
            try:
                avail_net_list = pAvailableNetworkList.contents
                networks = customresize(avail_net_list.Network, 
                                        avail_net_list.NumberOfItems)
                for network in networks:
                    print("SSID: {}, quality: {:2d}%".format(
                        network.dot11Ssid.SSID[:network.dot11Ssid.SSIDLength].decode(),
                        network.wlanSignalQuality))
            finally:
                WlanFreeMemory(pAvailableNetworkList)
    finally:
        WlanFreeMemory(pInterfaceList)