#!/bin/bash
function initialize
{
	sudo liquidctl --pick 0 initialize
	sudo liquidctl set fan speed 20 30  35 70  38 81  39 82  40 85  45 100
	
	tput clear;
	tput cup 0 0; printf "Watercooler initialized";
}

function assignDegreeToWavelength
{
	degree=$1	
	
	minimumDegree=34.2
	maximumDegree=43.5
	minimumWavelength=380
	maximumWavelength=780
	percentPosition=`echo "(($degree-$minimumDegree)*100/($maximumDegree-$minimumDegree))/100;" | bc -l`
	
	#tput cup 8 0; printf "Percent postioning $percentPosition"; 
	
	wavelength=`echo "$minimumWavelength*($percentPosition+1)" | bc -l`	
		
	#tput cup 9 0; printf "Percent postioning $wavelength"; 
	echo $wavelength
}

function normIntColor
{
	IntensityMax=$1
	factor=$2
	gamma=$3
	color=$4
		
	result=`python3 <<EOF
color = abs($color)
color = round($IntensityMax * pow(color * $factor, $gamma));
if color > 255:
	color = 255
elif color < 0:
	color = 0
print(color)
EOF`
	
	echo "$result"
}

function rgbToHexa
{
	red=$1
	green=$2
	blue=$3
			
	result=`python3 <<EOF
red = format($red, 'x');
green = format($green, 'x');
blue = format($blue, 'x');
list = [red,green,blue]

for x in range(len(list)):
	if len(list[x]) < 2:    	
		list[x] = "0" + list[x]

hexString = ""
for x in list:
	hexString = hexString + x

print(hexString)
EOF`
	
	echo "$result"
}

function wavelengthToRGB
{	
	wavelength=$1
	
	gamma=0.80;	IntensityMax=255; factor=0; red=0; green=0; blue=0;
	
	if (( $(echo "($wavelength >= 380) && ($wavelength<440)" |bc -l) )) 
	then
		red=`echo "($wavelength - 440) / (440 - 380); " | bc -l`
		green=0
		blue=1.0
	
	elif (( $(echo "($wavelength >= 440) && ($wavelength<490)" |bc -l) ))
	then
		red=0
		green=`echo "($wavelength - 440) / (490 - 440); " | bc -l`
		blue=1.0
	
	elif (( $(echo "($wavelength >= 490) && ($wavelength<510)" |bc -l) ))
	then
		red=0
		green=1.0
		blue=`echo "($wavelength - 510) / (510 - 490); " | bc -l`
	
	elif (( $(echo "($wavelength >= 510) && ($wavelength<580)" |bc -l) ))
	then
		red=`echo "($wavelength - 510) / (580 - 510); " | bc -l`		
		green=1.0
		blue=0
		
	elif (( $(echo "($wavelength >= 580) && ($wavelength<645)" |bc -l) ))
	then
		red=1.0
		green=`echo "($wavelength - 645) / (645 - 580); " | bc -l`
		blue=0
		
	elif (( $(echo "($wavelength >= 645) && ($wavelength<781)" |bc -l) ))
	then
		red=1.0
		green=0
		blue=0		
	fi	
	
	#tput cup 9 0; printf "Float Red $red"; 
	#tput cup 10 0; printf "Float Green $green"; 
	#tput cup 11 0; printf "Float Blue $blue"; 
	
	# Reduce intensity near the vision limits
	
	if (( $(echo "($wavelength >= 380) && ($wavelength<420)" |bc -l) )) 
	then
		factor=$(echo "0.3+0.7*($wavelength-380)/(420-380);" | bc )
		
	elif (( $(echo "($wavelength >= 420) && ($wavelength<701)" |bc -l) ))
	then
		factor=1.0
	
	elif (( $(echo "($wavelength >= 701) && ($wavelength<781)" |bc -l) ))
	then
		factor=$(echo "0.3+0.7*(780-$wavelength)/(780-700);" | bc )
	fi	
	
	#tput cup 12 0; printf "Calculated factor $factor"; 
	
	if (( $(echo "$red != 0" |bc -l) )) 
	then
		red=`normIntColor $IntensityMax $factor $gamma $red`
	fi
	
	#tput cup 13 0; printf "Calculated integer Red $red"; 
	
	if (( $(echo "$green != 0" |bc -l) )) 
	then	
		green=`normIntColor $IntensityMax $factor $gamma $green`
	fi
	
	#tput cup 14 0; printf "Calculated integer Green $green"; 
	
	if (( $(echo "$blue != 0" |bc -l) )) 
	then	
		blue=`normIntColor $IntensityMax $factor $gamma $blue`
	fi
	
	#tput cup 15 0; printf "Calculated integer Blue $blue"; 
	
	hexaRGB=`rgbToHexa $red $green $blue`
	
	#tput cup 16 0; printf "Calculated Hexa RGB $hexaRGB"; 
	
	echo "$hexaRGB"
}

function setLedColor
{
	#sudo liquidctl set led color fixed 006D6F
	liquid_temp=$1
	
	resultW=`assignDegreeToWavelength $liquid_temp`
	
	resultH=`wavelengthToRGB $resultW`
	
	tput cup 9 0; printf "Hexa RGB color $resultH"; 
	
	sudo liquidctl set led color fixed $resultH
	
	#if (( $(echo "$liquid_temp <= 25" |bc -l) )) 
	#then
	#	sudo liquidctl set led color fixed 2d5ff5 #azul
	#
	#elif (( $(echo "$liquid_temp <= 30" |bc -l) ))
	#then
	#	sudo liquidctl set led color fixed 0a91d9 #azul claro
	#
	#elif (( $(echo "$liquid_temp <= 35" |bc -l) ))
	#then
	#	sudo liquidctl set led color fixed 09baba #ciano
	#
	#elif (( $(echo "$liquid_temp <= 40" |bc -l) ))
	#then
	#	sudo liquidctl set led color fixed 08b00e #verde
	#	
	#elif (( $(echo "$liquid_temp <= 45" |bc -l) ))
	#then
	#	sudo liquidctl set led color fixed dae70a #amarelo lima
	#
	#elif (( $(echo "$liquid_temp <= 50" |bc -l) ))
	#then
	#	sudo liquidctl set led color fixed dec00a #amarelo escuro
	#
	#elif (( $(echo "$liquid_temp <= 55" |bc -l) ))
	#then
	#	sudo liquidctl set led color fixed f2800b #laranja
	#
	#elif (( $(echo "$liquid_temp <= 60" |bc -l) ))
	#then
	#	sudo liquidctl set led color fixed f0150b #vermelho
	#	
	#fi	
}
function setFanSpeed
{
	liquid_temp=$1
	
	if (( $(echo "$liquid_temp <= 30" |bc -l) )) 
	then
		speed=$( echo "scale=0;($liquid_temp+0.5)/1" | bc )
		sudo liquidctl set fan speed $speed
		tput cup 6 0; printf "Fan speed set to $speed per cent"; 
		
	elif (( $(echo "($liquid_temp > 30) && ($liquid_temp <= 40)" |bc -l) ))
	then
		temp=$( echo "$liquid_temp*(1+(0.09*($liquid_temp-30)))" | bc )
		speed=$( echo "scale=0;($temp+0.5)/1" | bc )
		sudo liquidctl set fan speed $speed		
		tput cup 6 0; printf "Fan speed set to $speed per cent"; 
		
	elif (( $(echo "($liquid_temp > 40) && ($liquid_temp <= 48)" |bc -l) ))
	then
		temp=$( echo "$liquid_temp*2.08" | bc )
		speed=$( echo "scale=0;($temp+0.5)/1" | bc )
		sudo liquidctl set fan speed $speed
		tput cup 6 0; printf "Fan speed set to $speed per cent"; 
		
	else 
		sudo liquidctl set fan 100
		tput cup 6 0; printf "Fan speed set to 100 per cent"; 
		
	fi
}


function status
{
	#sudo liquidctl --pick 0 status
	result=`sudo liquidctl --pick 0 status`	
	array=(`echo $result | sed 's/├/\n/g'`)	
	liquid_temp=${array[8]}
	fan_rpm=${array[13]}
	pump_rpm=${array[18]} 
	
	setLedColor $liquid_temp
	setFanSpeed $liquid_temp
	
	tput cup 2 0; tput el; printf "Liquid temp $liquid_temp"; 
	tput cup 3 0; tput el; printf "Fan rpm $fan_rpm"; 
	tput cup 4 0; tput el; printf "Pump rpm $pump_rpm";	
			
	sleep 3
}


let init_var=0

for (( ; ; ))
do
	if (($init_var == 0)) 
	then
		init_var=1
		initialize
	else
		status
	fi	
done