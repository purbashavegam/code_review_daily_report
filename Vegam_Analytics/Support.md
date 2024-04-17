##This document covers all mandatory points, to do an official release of a package from this repository.

### DIR structure
```
C:
│
└── VELO_FFT_service
    │
    ├── logs
    │
    ├── cert
    │
    ├── AnalyticsVelFFT.exe [ this is the executable for service ]
    │
    └── Vegam_MQTT.json

```


### How to make executable:
<details>
<summary>
  For service exe :
</summary>
<br>

- activate virtual env with provided <span style="color:green;">requirements_dev.txt</span> 
- run this command: 
```
pyinstaller --add-data "path to \AnalyticsJsonHandler.py;." --add-data "path to \AnalyticsMqtt.py;." --hidden-import paho.mqtt.client --hidden-import paho.mqtt.publish --hidden-import paho.mqtt.subscribe --hidden-import pandas --hidden-import scipy --onefile AnalyticsVelFFT.py
```

`check README for example case which is done in a local PC`

</details>
<details>
<summary>
  For data_generate_collet test file exe :
</summary>
<br>

```pyinstaller  --onefile data_generator_collector.py```
 
</details>


[comment]: <> (<span style="color:orange;">-purbasha</span>)

>###- [Points to be checked for next exe creation](#points to be checked for exe creation)
>1. folder is not working as package , but `__init__` file is present
>2. so, all py file need to added in exe command one by one
>3. it is getting created when venv is activated, but pip packages are not
   getting bundled up in exe.
 



### Click here to get soure code 👉  [Source code path](Software/src)
#



> ***This paths should not be changed to run the repo's code***
> 
> **Exe path:** C:\VELO_FFT_service 
> 
> **Log path:** C:\VELO_FFT_service\logs 
> 
> **Supporting Json path:** C:\VELO_FFT_service\Vegam_MQTT.json 
> 
> **ssl certificates path:** C:\VELO_FFT_service\cert
