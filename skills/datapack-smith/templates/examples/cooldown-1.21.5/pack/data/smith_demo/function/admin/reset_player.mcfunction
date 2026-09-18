execute unless score #ready sd.meta matches 1 run return fail
execute unless entity @s[type=minecraft:player] run return fail
scoreboard players set @s sd.cooldown 0
scoreboard players set @s sd.request 0
scoreboard players enable @s sd.request
return 1
