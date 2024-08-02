#!/bin/bash
echo 16 colors:
echo -e "\e[31mDefault background | Red foreground\e[39m"
echo -e "\e[42mGreen background | Default foreground\e[49m"
echo -e "\e[104;90mLight blue background | Dark gray foreground\e[39;49m"

echo 256 colors:
echo -e "\e[38;5;196mDefault background | Red foreground\e[39m"
echo -e "\e[48;5;22mGreen background | Default foreground\e[49m"
echo -e "\e[48;5;123;38;5;238mLight blue background | Dark gray foreground\e[39;49m"

echo RGB colors:
echo -e "\e[38;2;255;0;0mDefault background | Red foreground\e[39m"
echo -e "\e[48;2;0;128;0mGreen background | Default foreground\e[49m"
echo -e "\e[48;2;0;255;255m\e[38;2;255;0;255mCyan background | Magenta foreground\e[39;49m"
