# Online game ticks only; missing scores become zero without resetting progress.
scoreboard players add @a sd.cooldown 0
scoreboard players remove @a[scores={sd.cooldown=1..}] sd.cooldown 1
execute as @a at @s run function smith_demo:player/tick
