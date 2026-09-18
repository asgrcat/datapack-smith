# Internal: caller has checked the player, request and cooldown.
scoreboard players set @s sd.cooldown 100
particle minecraft:happy_villager ~ ~1 ~ 0.3 0.3 0.3 0 10 normal @s
tellraw @s {text:"発動しました。次は100オンラインtick後です。",color:"green"}
