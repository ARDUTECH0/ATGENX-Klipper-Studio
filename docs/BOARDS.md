# Supported boards

83 controller boards, generated from `boards/*.json`. Pin data comes from [Klipper's config files](https://github.com/Klipper3d/klipper/tree/master/config).

Board missing or wrong? See [CONTRIBUTING.md](../CONTRIBUTING.md#adding-or-fixing-a-board).

| Board | MCU | Drivers | TMC documented | Klipper file |
|---|---|---|---|---|
| Alligator R2 | sam3x8e | 7 | - | [generic-alligator-r2.cfg](https://github.com/Klipper3d/klipper/blob/master/config/generic-alligator-r2.cfg) |
| Alligator R3 | sam3x8e | 7 | - | [generic-alligator-r3.cfg](https://github.com/Klipper3d/klipper/blob/master/config/generic-alligator-r3.cfg) |
| BIGTREETECH E3 RRF V1.1 | STM32F407 | 4 | tmc2209 | [generic-bigtreetech-e3-rrf-v1.1.cfg](https://github.com/Klipper3d/klipper/blob/master/config/generic-bigtreetech-e3-rrf-v1.1.cfg) |
| BIGTREETECH GTR | STM32F407 | 6 | tmc2208, tmc2130, tmc5160 | [generic-bigtreetech-gtr.cfg](https://github.com/Klipper3d/klipper/blob/master/config/generic-bigtreetech-gtr.cfg) |
| BIGTREETECH Manta E3ez | STM32G0B1 | 5 | tmc2209, tmc2130 | [generic-bigtreetech-manta-e3ez.cfg](https://github.com/Klipper3d/klipper/blob/master/config/generic-bigtreetech-manta-e3ez.cfg) |
| BIGTREETECH Manta M4P | STM32G0B1 | 4 | tmc2209, tmc2130 | [generic-bigtreetech-manta-m4p.cfg](https://github.com/Klipper3d/klipper/blob/master/config/generic-bigtreetech-manta-m4p.cfg) |
| BIGTREETECH Manta M5P | STM32G0B1 | 5 | tmc2209, tmc2130 | [generic-bigtreetech-manta-m5p.cfg](https://github.com/Klipper3d/klipper/blob/master/config/generic-bigtreetech-manta-m5p.cfg) |
| BIGTREETECH Manta M8P V1.0 | STM32G0B1 | 8 | tmc2209, tmc2130 | [generic-bigtreetech-manta-m8p-v1.0.cfg](https://github.com/Klipper3d/klipper/blob/master/config/generic-bigtreetech-manta-m8p-v1.0.cfg) |
| BIGTREETECH Manta M8P V1.1 | STM32G0B1 | 8 | tmc2209, tmc2130 | [generic-bigtreetech-manta-m8p-v1.1.cfg](https://github.com/Klipper3d/klipper/blob/master/config/generic-bigtreetech-manta-m8p-v1.1.cfg) |
| BIGTREETECH Octopus Max EZ | STM32H723 | 10 | tmc2209, tmc2130 | [generic-bigtreetech-octopus-max-ez.cfg](https://github.com/Klipper3d/klipper/blob/master/config/generic-bigtreetech-octopus-max-ez.cfg) |
| BIGTREETECH Octopus Pro V1.0 | STM32F446, STM32F429, STM32H723 | 8 | tmc2209, tmc2130 | [generic-bigtreetech-octopus-pro-v1.0.cfg](https://github.com/Klipper3d/klipper/blob/master/config/generic-bigtreetech-octopus-pro-v1.0.cfg) |
| BIGTREETECH Octopus Pro V1.1 | STM32H723 | 8 | tmc2209, tmc2130 | [generic-bigtreetech-octopus-pro-v1.1.cfg](https://github.com/Klipper3d/klipper/blob/master/config/generic-bigtreetech-octopus-pro-v1.1.cfg) |
| BIGTREETECH Octopus V1.1 | STM32F446, STM32F429 | 8 | tmc2209, tmc2130 | [generic-bigtreetech-octopus-v1.1.cfg](https://github.com/Klipper3d/klipper/blob/master/config/generic-bigtreetech-octopus-v1.1.cfg) |
| BIGTREETECH SKR 2 | STM32F407, STM32F429 | 5 | tmc2209, tmc2130 | [generic-bigtreetech-skr-2.cfg](https://github.com/Klipper3d/klipper/blob/master/config/generic-bigtreetech-skr-2.cfg) |
| BIGTREETECH SKR 3 | STM32H743, STM32H723 | 5 | tmc2209, tmc2130 | [generic-bigtreetech-skr-3.cfg](https://github.com/Klipper3d/klipper/blob/master/config/generic-bigtreetech-skr-3.cfg) |
| BIGTREETECH SKR CR6 V1.0 | STM32F103 | 4 | tmc2209 | [generic-bigtreetech-skr-cr6-v1.0.cfg](https://github.com/Klipper3d/klipper/blob/master/config/generic-bigtreetech-skr-cr6-v1.0.cfg) |
| BIGTREETECH SKR E3 DIP | STM32F103 | 4 | tmc2208, tmc2130 | [generic-bigtreetech-skr-e3-dip.cfg](https://github.com/Klipper3d/klipper/blob/master/config/generic-bigtreetech-skr-e3-dip.cfg) |
| BIGTREETECH SKR E3 Turbo | lpc1769 | 5 | tmc2209 | [generic-bigtreetech-skr-e3-turbo.cfg](https://github.com/Klipper3d/klipper/blob/master/config/generic-bigtreetech-skr-e3-turbo.cfg) |
| BIGTREETECH SKR Mini | STM32F103 | 4 | - | [generic-bigtreetech-skr-mini.cfg](https://github.com/Klipper3d/klipper/blob/master/config/generic-bigtreetech-skr-mini.cfg) |
| BIGTREETECH SKR Mini E3 V1.0 | STM32F103 | 4 | tmc2209 | [generic-bigtreetech-skr-mini-e3-v1.0.cfg](https://github.com/Klipper3d/klipper/blob/master/config/generic-bigtreetech-skr-mini-e3-v1.0.cfg) |
| BIGTREETECH SKR Mini E3 V1.2 | STM32F103 | 4 | tmc2209 | [generic-bigtreetech-skr-mini-e3-v1.2.cfg](https://github.com/Klipper3d/klipper/blob/master/config/generic-bigtreetech-skr-mini-e3-v1.2.cfg) |
| BIGTREETECH SKR Mini E3 V2.0 | STM32F103 | 4 | tmc2209 | [generic-bigtreetech-skr-mini-e3-v2.0.cfg](https://github.com/Klipper3d/klipper/blob/master/config/generic-bigtreetech-skr-mini-e3-v2.0.cfg) |
| BIGTREETECH SKR Mini E3 V3.0 | STM32G0B1 | 4 | tmc2209 | [generic-bigtreetech-skr-mini-e3-v3.0.cfg](https://github.com/Klipper3d/klipper/blob/master/config/generic-bigtreetech-skr-mini-e3-v3.0.cfg) |
| BIGTREETECH SKR Mini MZ | STM32F103 | 4 | tmc2209 | [generic-bigtreetech-skr-mini-mz.cfg](https://github.com/Klipper3d/klipper/blob/master/config/generic-bigtreetech-skr-mini-mz.cfg) |
| BIGTREETECH SKR Pico V1.0 | rp2040 | 4 | tmc2209 | [generic-bigtreetech-skr-pico-v1.0.cfg](https://github.com/Klipper3d/klipper/blob/master/config/generic-bigtreetech-skr-pico-v1.0.cfg) |
| BIGTREETECH SKR Pro | STM32F407 | 6 | tmc2208, tmc2130 | [generic-bigtreetech-skr-pro.cfg](https://github.com/Klipper3d/klipper/blob/master/config/generic-bigtreetech-skr-pro.cfg) |
| BIGTREETECH SKR V1.1 | lpc1768 | 5 | - | [generic-bigtreetech-skr-v1.1.cfg](https://github.com/Klipper3d/klipper/blob/master/config/generic-bigtreetech-skr-v1.1.cfg) |
| BIGTREETECH SKR V1.3 | lpc1768 | 5 | tmc2208, tmc2130 | [generic-bigtreetech-skr-v1.3.cfg](https://github.com/Klipper3d/klipper/blob/master/config/generic-bigtreetech-skr-v1.3.cfg) |
| BIGTREETECH SKR V1.4 | lpc1769, lpc1768 | 5 | tmc2208, tmc2130 | [generic-bigtreetech-skr-v1.4.cfg](https://github.com/Klipper3d/klipper/blob/master/config/generic-bigtreetech-skr-v1.4.cfg) |
| CRAMPS | beaglebone, pru | 4 | - | [generic-cramps.cfg](https://github.com/Klipper3d/klipper/blob/master/config/generic-cramps.cfg) |
| Creality V4.2.10 | STM32F103 | 4 | tmc2208 | [generic-creality-v4.2.10.cfg](https://github.com/Klipper3d/klipper/blob/master/config/generic-creality-v4.2.10.cfg) |
| Creality V4.2.7 | STM32F103 | 4 | - | [generic-creality-v4.2.7.cfg](https://github.com/Klipper3d/klipper/blob/master/config/generic-creality-v4.2.7.cfg) |
| Duet3D Duet2 | sam4e8e | 5 | tmc2660 | [generic-duet2.cfg](https://github.com/Klipper3d/klipper/blob/master/config/generic-duet2.cfg) |
| Duet3D Duet2 Duex | sam4e8e | 10 | tmc2660 | [generic-duet2-duex.cfg](https://github.com/Klipper3d/klipper/blob/master/config/generic-duet2-duex.cfg) |
| Duet3D Duet2 Maestro | sam4s8c | 5 | tmc2208 | [generic-duet2-maestro.cfg](https://github.com/Klipper3d/klipper/blob/master/config/generic-duet2-maestro.cfg) |
| Duet3D Duet3 6hc | same70q20b | 4 | tmc5160 | [generic-duet3-6hc.cfg](https://github.com/Klipper3d/klipper/blob/master/config/generic-duet3-6hc.cfg) |
| Duet3D Duet3 6xd | same70q20b | 4 | - | [generic-duet3-6xd.cfg](https://github.com/Klipper3d/klipper/blob/master/config/generic-duet3-6xd.cfg) |
| Duet3D Duet3 Mini | atsam | 4 | tmc2209 | [generic-duet3-mini.cfg](https://github.com/Klipper3d/klipper/blob/master/config/generic-duet3-mini.cfg) |
| FlyBoard | STM32F407 | 8 | tmc2208, tmc2130 | [generic-flyboard.cfg](https://github.com/Klipper3d/klipper/blob/master/config/generic-flyboard.cfg) |
| FYSETC Cheetah V1.1 | STM32F103 | 4 | tmc2209 | [generic-fysetc-cheetah-v1.1.cfg](https://github.com/Klipper3d/klipper/blob/master/config/generic-fysetc-cheetah-v1.1.cfg) |
| FYSETC Cheetah V1.2 | STM32F103 | 4 | tmc2208 | [generic-fysetc-cheetah-v1.2.cfg](https://github.com/Klipper3d/klipper/blob/master/config/generic-fysetc-cheetah-v1.2.cfg) |
| FYSETC Cheetah V2.0 | STM32F401 | 4 | tmc2209 | [generic-fysetc-cheetah-v2.0.cfg](https://github.com/Klipper3d/klipper/blob/master/config/generic-fysetc-cheetah-v2.0.cfg) |
| FYSETC F6 | atmega2560 | 6 | tmc2208, tmc2130 | [generic-fysetc-f6.cfg](https://github.com/Klipper3d/klipper/blob/master/config/generic-fysetc-f6.cfg) |
| FYSETC S6 | STM32F446 | 6 | tmc2208, tmc2130 | [generic-fysetc-s6.cfg](https://github.com/Klipper3d/klipper/blob/master/config/generic-fysetc-s6.cfg) |
| FYSETC S6 V2 | STM32F446 | 6 | tmc2208, tmc2130 | [generic-fysetc-s6-v2.cfg](https://github.com/Klipper3d/klipper/blob/master/config/generic-fysetc-s6-v2.cfg) |
| FYSETC Spider | STM32F446 | 8 | tmc2208, tmc2130 | [generic-fysetc-spider.cfg](https://github.com/Klipper3d/klipper/blob/master/config/generic-fysetc-spider.cfg) |
| Geeetech GT2560 | atmega2560 | 4 | - | [generic-gt2560.cfg](https://github.com/Klipper3d/klipper/blob/master/config/generic-gt2560.cfg) |
| I3DBEEZ9 | STM32F407 | 7 | tmc2208, tmc2130 | [generic-I3DBEEZ9.cfg](https://github.com/Klipper3d/klipper/blob/master/config/generic-I3DBEEZ9.cfg) |
| LDO Leviathan V1.2 | STM32F446 | 7 | tmc5160, tmc2209 | [generic-ldo-leviathan-v1.2.cfg](https://github.com/Klipper3d/klipper/blob/master/config/generic-ldo-leviathan-v1.2.cfg) |
| Makerbase Monster8 | STM32F407 | 8 | tmc2208, tmc2130 | [generic-mks-monster8.cfg](https://github.com/Klipper3d/klipper/blob/master/config/generic-mks-monster8.cfg) |
| Makerbase Robin E3 | STM32F103 | 4 | tmc2209 | [generic-mks-robin-e3.cfg](https://github.com/Klipper3d/klipper/blob/master/config/generic-mks-robin-e3.cfg) |
| Makerbase Robin Nano V1 | STM32F103 | 5 | - | [generic-mks-robin-nano-v1.cfg](https://github.com/Klipper3d/klipper/blob/master/config/generic-mks-robin-nano-v1.cfg) |
| Makerbase Robin Nano V2 | STM32F103 | 5 | - | [generic-mks-robin-nano-v2.cfg](https://github.com/Klipper3d/klipper/blob/master/config/generic-mks-robin-nano-v2.cfg) |
| Makerbase Robin Nano V3 | STM32F407 | 5 | - | [generic-mks-robin-nano-v3.cfg](https://github.com/Klipper3d/klipper/blob/master/config/generic-mks-robin-nano-v3.cfg) |
| Makerbase Rumba32 V1.0 | STM32F446 | 6 | tmc2209 | [generic-mks-rumba32-v1.0.cfg](https://github.com/Klipper3d/klipper/blob/master/config/generic-mks-rumba32-v1.0.cfg) |
| Makerbase SGENL | lpc1768 | 5 | tmc2208, tmc2130 | [generic-mks-sgenl.cfg](https://github.com/Klipper3d/klipper/blob/master/config/generic-mks-sgenl.cfg) |
| Mellow Fly CDY V3 | STM32F407 | 6 | tmc2209, tmc5160 | [generic-mellow-fly-cdy-v3.cfg](https://github.com/Klipper3d/klipper/blob/master/config/generic-mellow-fly-cdy-v3.cfg) |
| Mellow Fly E3 V2 | STM32F407 | 5 | tmc2209 | [generic-mellow-fly-e3-v2.cfg](https://github.com/Klipper3d/klipper/blob/master/config/generic-mellow-fly-e3-v2.cfg) |
| Mellow Fly Gemini V1 | STM32F405 | 4 | tmc2209, tmc5160 | [generic-mellow-fly-gemini-v1.cfg](https://github.com/Klipper3d/klipper/blob/master/config/generic-mellow-fly-gemini-v1.cfg) |
| Mellow Fly Gemini V2 | STM32F405 | 4 | tmc2209, tmc5160 | [generic-mellow-fly-gemini-v2.cfg](https://github.com/Klipper3d/klipper/blob/master/config/generic-mellow-fly-gemini-v2.cfg) |
| Mellow Super Infinty HV | STM32F407 | 8 | tmc2208, tmc5160 | [generic-mellow-super-infinty-hv.cfg](https://github.com/Klipper3d/klipper/blob/master/config/generic-mellow-super-infinty-hv.cfg) |
| Melzi | atmega1284p | 4 | - | [generic-melzi.cfg](https://github.com/Klipper3d/klipper/blob/master/config/generic-melzi.cfg) |
| MightyBoard | atmega1280 | 4 | - | [generic-mightyboard.cfg](https://github.com/Klipper3d/klipper/blob/master/config/generic-mightyboard.cfg) |
| Minitronics 1.0 | atmega1280, atmega1281 | 4 | - | [generic-minitronics1.cfg](https://github.com/Klipper3d/klipper/blob/master/config/generic-minitronics1.cfg) |
| Ruramps V1.3 | sam3x8e | 5 | - | [generic-ruramps-v1.3.cfg](https://github.com/Klipper3d/klipper/blob/master/config/generic-ruramps-v1.3.cfg) |
| Panucatt Azteeg X5 Mini V3 | lpc1769 | 4 | - | [generic-azteeg-x5-mini-v3.cfg](https://github.com/Klipper3d/klipper/blob/master/config/generic-azteeg-x5-mini-v3.cfg) |
| Re-ARM | lpc1768 | 5 | - | [generic-re-arm.cfg](https://github.com/Klipper3d/klipper/blob/master/config/generic-re-arm.cfg) |
| Printrbot Printrboard | at90usb1286 | 4 | - | [generic-printrboard.cfg](https://github.com/Klipper3d/klipper/blob/master/config/generic-printrboard.cfg) |
| Printrbot Printrboard G2 | atsam | 4 | - | [generic-printrboard-g2.cfg](https://github.com/Klipper3d/klipper/blob/master/config/generic-printrboard-g2.cfg) |
| Prusa Buddy | STM32F407 | 4 | tmc2209 | [generic-prusa-buddy.cfg](https://github.com/Klipper3d/klipper/blob/master/config/generic-prusa-buddy.cfg) |
| Prusa Einsy Rambo | atmega2560 | 4 | tmc2130 | [generic-einsy-rambo.cfg](https://github.com/Klipper3d/klipper/blob/master/config/generic-einsy-rambo.cfg) |
| RADDS | sam3x8e | 6 | - | [generic-radds.cfg](https://github.com/Klipper3d/klipper/blob/master/config/generic-radds.cfg) |
| RAMPS 1.4 | atmega2560, atmega1280 | 5 | - | [generic-ramps.cfg](https://github.com/Klipper3d/klipper/blob/master/config/generic-ramps.cfg) |
| RemRam | STM32F765 | 4 | tmc2130 | [generic-remram.cfg](https://github.com/Klipper3d/klipper/blob/master/config/generic-remram.cfg) |
| Replicape | beaglebone, pru | 4 | - | [generic-replicape.cfg](https://github.com/Klipper3d/klipper/blob/master/config/generic-replicape.cfg) |
| RUMBa | atmega2560 | 6 | - | [generic-rumba.cfg](https://github.com/Klipper3d/klipper/blob/master/config/generic-rumba.cfg) |
| Smoothieware Smoothieboard | lpc176x | 5 | - | [generic-smoothieboard.cfg](https://github.com/Klipper3d/klipper/blob/master/config/generic-smoothieboard.cfg) |
| TH3D Ezboard Lite V1.2 | lpc1769 | 4 | tmc2208 | [generic-th3d-ezboard-lite-v1.2.cfg](https://github.com/Klipper3d/klipper/blob/master/config/generic-th3d-ezboard-lite-v1.2.cfg) |
| TH3D Ezboard V2.0 | STM32F405 | 4 | tmc2209 | [generic-th3d-ezboard-v2.0.cfg](https://github.com/Klipper3d/klipper/blob/master/config/generic-th3d-ezboard-v2.0.cfg) |
| Ultimachine Archim2 | sam3x8e | 5 | tmc2130 | [generic-archim2.cfg](https://github.com/Klipper3d/klipper/blob/master/config/generic-archim2.cfg) |
| Ultimachine Mini Rambo | atmega2560 | 4 | - | [generic-mini-rambo.cfg](https://github.com/Klipper3d/klipper/blob/master/config/generic-mini-rambo.cfg) |
| Ultimachine Rambo | atmega2560 | 5 | - | [generic-rambo.cfg](https://github.com/Klipper3d/klipper/blob/master/config/generic-rambo.cfg) |
| Ultimaker Ultimainboard V2 | atmega2560 | 5 | - | [generic-ultimaker-ultimainboard-v2.cfg](https://github.com/Klipper3d/klipper/blob/master/config/generic-ultimaker-ultimainboard-v2.cfg) |
