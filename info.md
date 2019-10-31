# Custom components for Home Assistant
## BKK stop custom component and state card

This custom component and custom state card shows Budapest Public Transportation (BKK)
line information departing in the near future from a configurable stop.

#### Configuration variables:
**name** (Optional): Name of component<br />
**stopId** (Required): StopId as per [futar.bkk.hu](http://futar.bkk.hu)<br />
**minsAfter** (Optional): Number of minutes ahead to show vehicles departing from station (default: 20)<br />
**wheelchair** (Optional): Display vehicle's wheelchair accessibility (default: false)<br />
**bikes** (Optional): Display whether bikes are allowed on vehicle (default: false)<br />
**ignoreNow** (Optional): Ignore vehicles already in the station (default: false) <br />

Custom Lovelace card can be found:
https://github.com/au190/au190_bkk_stop_card

#### How to get StopId:
Visit [futar.bkk.hu](http://futar.bkk.hu) and select your stop, then copy the id:


```
#***********************************************************************
#   https://futar.bkk.hu/route/
#***********************************************************************
sensor:
  - platform: au190_bkk_stop_1
    name: '99_Home_City'
    stopId: 'BKK_F04097'
    wheelchair: false
    minsAfter: 20 
    ignoreNow: false
    
  - platform: au190_bkk_stop_1
    name: '99_VajdaPéter_Home'
    stopId: 'BKK_F01260'
    
  - platform: au190_bkk_stop_1
    name: '99_Tess_Home'
    stopId: 'BKK_F04171'

  - platform: au190_bkk_stop_1
    name: '99_Blaha_Home'
    stopId: 'BKK_F01294'
    
  - platform: au190_bkk_stop_1
    name: '23_Boráros_Home'
    stopId: 'BKK_008546'

  - platform: au190_bkk_stop_1
    name: '23_Home_City'
    stopId: 'BKK_F04094'
    
```

#### Example card:
<img src='https://raw.githubusercontent.com/au190/au190_bkk_stop/master/bkk_lovelace.png'/>


Updated server side
Updated client side (shows when was updated)
Original: https://github.com/amaximus/bkk-stop-card
