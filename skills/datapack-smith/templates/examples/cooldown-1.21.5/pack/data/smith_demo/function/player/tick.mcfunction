# Only input value 1 is accepted. Invalid or cooling-down requests are discarded.
execute if score @s sd.request matches 1 if score @s sd.cooldown matches 0 run function smith_demo:player/activate
scoreboard players set @s sd.request 0
scoreboard players enable @s sd.request
