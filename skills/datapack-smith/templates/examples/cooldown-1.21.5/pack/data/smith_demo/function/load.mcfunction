# Repeated objective creation may fail; existing scores remain intact.
scoreboard objectives add sd.meta dummy
scoreboard objectives add sd.cooldown dummy
scoreboard objectives add sd.request trigger
scoreboard players add #schema sd.meta 0
execute if score #schema sd.meta matches 0 run scoreboard players set #schema sd.meta 1
scoreboard players set #ready sd.meta 0
execute unless score #schema sd.meta matches 1 run return fail
scoreboard players set #ready sd.meta 1
say SMITH_DEMO_LOAD_OK
