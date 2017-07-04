from fuzzywuzzy import fuzz
import csv
from glob import glob




#Read in Zipcode data
zipcodes = {'zipcode':[], 'lat':[], 'long':[]}

with open('zipcodedata/zip_code_database.csv') as csvfile:
	reader = csv.DictReader(csvfile, fieldnames=['zipcode', 'lat', 'long'])
	for row in reader:
		#print row['zipcode']
		zipcodes['zipcode'].append(row['zipcode'])
		zipcodes['lat'].append(float(row['lat']))
		zipcodes['long'].append(float(row['long']))




#Read in EPA data
epa_data = {'make-model':[], 'year':[], 'city':[], 'highway':[], 'combined':[]}

files = glob('epadata/*.csv')
for f in files:
	with open(f) as csvfile:
		reader = csv.DictReader(csvfile, fieldnames=['year', 'make', 'model', 'city', 'highway', 'combined'])
		for row in reader:
			make_model = '{}{}'.format(row['make'], row['model'])
			make_model = filter(str.isalnum, make_model)
			make_model = make_model.upper()
			epa_data['year'].append(row['year']) 
			epa_data['make-model'].append(make_model)
			epa_data['city'].append(row['city'])
			epa_data['highway'].append(row['highway'])
			epa_data['combined'].append(row['combined'])




#Read in CRC Employee Data, Calculate distance per trip, match with fuel efficencies
driver_data = {'zipcode':[], 'make-model':[], 'year':[], 'status':[], 'distance':[], 'city':[], 'highway':[], 'combined':[]}

#Total number of facutly data points read
total = 0
#Number of data points skipped because zipcode couldn't be found or car model couldn't be identified 
full_time_skipped = 0
part_time_skipped = 0

#Lat and long of Charles River Campus
BASE_LAT = 42.35
BASE_LONG = -71.11

with open('budata/CRCEmployeePermit.csv') as csvfile:
	reader = csv.DictReader(csvfile, fieldnames=['make', 'model', 'year', 'zipcode', 'status'])
	for row in reader:
		total = total + 1
		try:
			#Find Zipcode
			zip_lat = zipcodes['lat'][zipcodes['zipcode'].index(row['zipcode'])]
			zip_long = zipcodes['long'][zipcodes['zipcode'].index(row['zipcode'])]
			
			#Calculate Distance Traveled
			distance = ((69 * abs(BASE_LAT - zip_lat)) ** 2 + (51 * abs(BASE_LONG - zip_long)) ** 2) ** 0.5
			
			#Read Fuel Economy based on make and model
			make_model = "{}{}".format(row['make'], row['model'])
			make_model = make_model.replace("+AC0", "")
			make_model = filter(str.isalnum, make_model)
			make_model = make_model.upper()

			#Get all cars make in year of this car from epa data
			year_matches = [j for j, x in enumerate(epa_data['year']) if x == row['year']]
			indecies = []
			ratios = []
			#Loop through make-model of cars make in that year
			#Find make-model in epa data that most closely matches matches make-model read in
			for year_match in year_matches:
				ratio = fuzz.ratio(epa_data['make-model'][year_match], make_model)
				if ratio > 80:
					ratios.append(ratio)
					indecies.append(year_match)
			index = indecies[ratios.index(max(ratios))]

			#Get fuel economies for that make model and add to driver dataset
			driver_data['city'].append(float(epa_data['city'][index]))
			driver_data['highway'].append(float(epa_data['highway'][index]))
			driver_data['combined'].append(float(epa_data['combined'][index]))
			
			#Add zipcode and distance
			driver_data['distance'].append(distance) 
			driver_data['zipcode'].append(row['zipcode'])

			#Add Make-Model		
			driver_data['make-model'].append(make_model)
			
			#Add Year		
			driver_data['year'].append(row['year'])
	
			#Add Employee Status
			driver_data['status'].append(filter(str.isalnum, row['status']).upper())

		except:
			#If zipcode is invalid or make-model not found, skip
			status = filter(str.isalnum, row['status']).upper()
			if "PART" in status:
				part_time_skipped = part_time_skipped + 1
			else:
				full_time_skipped = full_time_skipped + 1




#Write out formated CSV containing all datapoints
#This is if someone wants to look at the raw data, mostly for debugging
with open('output_csvs/crc_employee_full.csv', 'w') as csvfile:
	writer = csv.DictWriter(csvfile, fieldnames=['zipcode', 'make-model', 'year', 'status', 'distance', 'city', 'highway', 'combined'])
	 
	for i in range(0, len(driver_data['status'])):
		writer.writerow({
			'status':driver_data['status'][i],
			'zipcode':driver_data['zipcode'][i],
			'distance':driver_data['distance'][i],
			'make-model':driver_data['make-model'][i],
			'year':driver_data['year'][i],
			'city':driver_data['city'][i],
			'highway':driver_data['highway'][i],
			'combined':driver_data['combined'][i]
		})




#Calculate CO2 Summary data for charles river campus
#Static value, pounds of co2 release per gallon of gas used
CO2_per_gallon = 20

#Because cars were skipped, we have to make an estimate of what thier distance/fuel economy was
#We also don't know the make/model/year of drivers on the medical campus
#So take the average fuel economies
fuel_economies = {}
fuel_economies['avg_city'] = float(sum(driver_data['city']))/float(len(driver_data['city']))
fuel_economies['avg_highway'] = float(sum(driver_data['highway']))/float(len(driver_data['highway']))
fuel_economies['avg_combined'] = float(sum(driver_data['combined']))/float(len(driver_data['combined']))

#distances traveled by CRC drivers
distances = {}
#Distance sums
distances['sum'] = float(sum(driver_data['distance']))
distances['sum_part_time'] = float(sum([distance for i, distance in enumerate(driver_data['distance']) if "PART" in driver_data['status'][i]]))
distances['sum_full_time'] = float(sum([distance for i, distance in enumerate(driver_data['distance']) if "PART" not in driver_data['status'][i]]))

#Distance averages
distances['avg'] = float(sum(driver_data['distance']))/float(len(driver_data['distance']))
distances['avg_part_time'] = float(sum([distance for i, distance in enumerate(driver_data['distance']) if "PART" in driver_data['status'][i]])) / float(len([distance for i, distance in enumerate(driver_data['distance']) if "PART" in driver_data['status'][i]]))
distances['avg_full_time'] = float(sum([distance for i, distance in enumerate(driver_data['distance']) if "PART" not in driver_data['status'][i]])) / float(len([distance for i, distance in enumerate(driver_data['distance']) if "PART" not in driver_data['status'][i]])) 


#CO2 Metrics
metrics = {}
metrics['city_10'] = 0 #highest co2 estimate, assume 10 trips/week with city millage
metrics['highway_10'] = 0 #10 trips per week with highway millage
metrics['combined_10'] = 0 #10 trips/week with combined millage
metrics['city_6'] = 0 #6 trips/week with city millage
metrics['highway_6'] = 0 #lowest co2 estimate, 6 trips per week with highway millage
metrics['combined_6'] = 0 #6 trips per week with combined millage
metrics['best_guess'] = 0 #best estimate, uses combined fe, 6 trips/week if employee has part time status, 10 trips/week if full time

#Populate metrics
for i, status in enumerate(driver_data['status']):
	metrics['city_10'] = metrics['city_10'] + (10 * driver_data['distance'][i]/driver_data['city'][i]) * CO2_per_gallon
	metrics['highway_10'] = metrics['highway_10'] + (10 * driver_data['distance'][i]/driver_data['highway'][i]) * CO2_per_gallon
	metrics['city_6'] = metrics['city_6'] + (6 * driver_data['distance'][i]/driver_data['city'][i]) * CO2_per_gallon
	metrics['highway_6'] = metrics['highway_6'] + (6 * driver_data['distance'][i]/driver_data['highway'][i]) * CO2_per_gallon
	metrics['combined_10'] = metrics['combined_10'] + (10 * driver_data['distance'][i]/driver_data['combined'][i]) * CO2_per_gallon
	metrics['combined_6'] = metrics['combined_6'] + (6 * driver_data['distance'][i]/driver_data['combined'][i]) * CO2_per_gallon
	if "PART" in status:
		#If part time assume 6 trips per week
		metrics['best_guess'] = metrics['best_guess'] + (6 * driver_data['distance'][i]/driver_data['combined'][i]) * CO2_per_gallon
	else:
		#If full time assume 10 trips per week
		metrics['best_guess'] = metrics['best_guess'] + (10 * driver_data['distance'][i]/driver_data['combined'][i]) * CO2_per_gallon


#Here is where the estimating comes in
#Upper error is going to be the value calculated in the above for loop plus the min measured fuel economy * max measured distance * #skipped
#Min fuel economy because lowest fuel economy produces highest co2
fuel_economies['max_combined'] = min(driver_data['combined']) #Max co2 production is going to be min fuel economy
fuel_economies['max_city'] = min(driver_data['city'])
fuel_economies['max_highway'] = min(driver_data['highway'])

#Distance Maxes
distances['max'] = max(driver_data['distance']) #Used for debugging not calculations
distances['max_part_time'] = max([distance for i, distance in enumerate(driver_data['distance']) if "PART" in driver_data['status'][i]])
distances['max_full_time'] = max([distance for i, distance in enumerate(driver_data['distance']) if "PART" not in driver_data['status'][i]])

upper_error = {}
upper_error['best_guess'] = metrics['best_guess'] + (6 * distances['max_part_time']/fuel_economies['max_city'] * part_time_skipped + 10 * distances['max_full_time']/fuel_economies['max_city'] * full_time_skipped) * CO2_per_gallon
upper_error['city_10'] = metrics['city_10'] + 10 * distances['max']/fuel_economies['max_city'] * (part_time_skipped + full_time_skipped) * CO2_per_gallon
upper_error['combined_10'] = metrics['combined_10'] + 10 * distances['max']/fuel_economies['max_combined'] * (part_time_skipped + full_time_skipped) * CO2_per_gallon
upper_error['highway_10'] = metrics['highway_10'] + 10 * distances['max']/fuel_economies['max_highway'] * (part_time_skipped + full_time_skipped) * CO2_per_gallon
upper_error['city_6'] = metrics['city_6'] + 6 * distances['max']/fuel_economies['max_city'] * (part_time_skipped + full_time_skipped) * CO2_per_gallon
upper_error['combined_6'] = metrics['combined_6'] + 6 * distances['max']/fuel_economies['max_combined'] * (part_time_skipped + full_time_skipped) * CO2_per_gallon
upper_error['highway_6'] = metrics['highway_6'] + 6 * distances['max']/fuel_economies['max_highway'] * (part_time_skipped + full_time_skipped) * CO2_per_gallon
 
#Lower error is going to be the value calculated in the above for loop plus the max of fe * min distance * #skipped
#Max fuel economy will produce min co2
fuel_economies['min_combined'] = max(driver_data['combined']) #Max co2 production is going to be min fuel economy
fuel_economies['min_city'] = max(driver_data['city'])
fuel_economies['min_highway'] = max(driver_data['highway'])

#Distance mins
distances['min'] = min(driver_data['distance'])
distances['min_part_time'] = min([distance for i, distance in enumerate(driver_data['distance']) if "PART" in driver_data['status'][i]])
distances['min_full_time'] = min([distance for i, distance in enumerate(driver_data['distance']) if "PART" not in driver_data['status'][i]])

lower_error = {}
lower_error['best_guess'] = metrics['best_guess'] + (6 * distances['min_part_time']/fuel_economies['min_highway'] * part_time_skipped + 10 * distances['min_full_time']/fuel_economies['min_highway'] * full_time_skipped) * CO2_per_gallon
lower_error['city_10'] = metrics['city_10'] + 10 * distances['min']/fuel_economies['min_city'] * (part_time_skipped + full_time_skipped) * CO2_per_gallon
lower_error['combined_10'] = metrics['combined_10'] + 10 * distances['min']/fuel_economies['min_combined'] * (part_time_skipped + full_time_skipped) * CO2_per_gallon
lower_error['highway_10'] = metrics['highway_10'] + 10 * distances['min']/fuel_economies['min_highway'] * (part_time_skipped + full_time_skipped) * CO2_per_gallon
lower_error['city_6'] = metrics['city_6'] + 6 * distances['min']/fuel_economies['min_city'] * (part_time_skipped + full_time_skipped) * CO2_per_gallon
lower_error['combined_6'] = metrics['combined_6'] + 6 * distances['min']/fuel_economies['min_combined'] * (part_time_skipped + full_time_skipped) * CO2_per_gallon
lower_error['highway_6'] = metrics['highway_6'] + 6 * distances['min']/fuel_economies['min_highway'] * (part_time_skipped + full_time_skipped) * CO2_per_gallon


#the actual co2 metric is going to be the value calculated in above for loop plus the average of fe * average of distance * #skipped
metrics['best_guess'] = metrics['best_guess'] + (6 * distances['avg_part_time']/fuel_economies['avg_combined'] * part_time_skipped + 10 * distances['avg_full_time']/fuel_economies['avg_combined'] * full_time_skipped) * CO2_per_gallon
metrics['city_10'] = metrics['city_10'] + 10 * distances['avg']/fuel_economies['avg_city'] * (part_time_skipped + full_time_skipped) * CO2_per_gallon
metrics['highway_10'] = metrics['highway_10'] + 10 * distances['avg']/fuel_economies['avg_highway'] * (part_time_skipped + full_time_skipped) * CO2_per_gallon
metrics['city_6'] = metrics['city_6'] + 6 * distances['avg']/fuel_economies['avg_city'] * (part_time_skipped + full_time_skipped) * CO2_per_gallon
metrics['highway_6'] = metrics['highway_6'] + 6 * distances['avg']/fuel_economies['avg_highway'] * (part_time_skipped + full_time_skipped) * CO2_per_gallon
metrics['combined_10'] = metrics['combined_10'] + 10 * distances['avg']/fuel_economies['avg_combined'] * (part_time_skipped + full_time_skipped) * CO2_per_gallon
metrics['combined_6'] = metrics['combined_6'] + 6 * distances['avg']/fuel_economies['avg_combined'] * (part_time_skipped + full_time_skipped) * CO2_per_gallon



#Print Summary Data
print "CRC Summary Data"
print "Total {}, full time skipped {}, part time skipped {}".format(total, full_time_skipped, part_time_skipped)
for key, value in metrics.iteritems():
	print "metric {}: lower limit {}, metric {}, higher limit {}".format(key, lower_error[key], value, upper_error[key])
for key, value in distances.iteritems():
	print "distance {}: {}".format(key, value)  


#Generate graph file
with open("graph_data.csv", "w") as csvfile:
	writer = csv.DictWriter(csvfile, fieldnames=['group', 'lower_error', 'metric', 'upper_error'])
	writer.writeheader()
	writer.writerow({'group':'crc_employee', 'lower_error':lower_error['best_guess'], 'metric':metrics['best_guess'], 'upper_error':upper_error['best_guess']})

#Read in Medical Campus Employee Data
#Same as with CRC except that we don't know make/model of car, so fe values are just average of crc data
driver_data = {'status':[], 'zipcode':[], 'distance':[], 'city':[], 'highway':[], 'combined':[]}

#Lat and long of medical campus
BASE_LAT = 42.34 
BASE_LONG = -71.07

part_time_skipped = 0
full_time_skipped = 0
total = 0
with open('budata/MEDEmployeePermit.csv') as csvfile:
	reader = csv.DictReader(csvfile, fieldnames=['zipcode', 'status'])
	for row in reader:
		total = total + 1
		try:
			#Calculate distance traveled 
			zip_lat = zipcodes['lat'][zipcodes['zipcode'].index(row['zipcode'])]
			zip_long = zipcodes['long'][zipcodes['zipcode'].index(row['zipcode'])]
			distance = ((69 * abs(BASE_LAT - zip_lat)) ** 2 + (51 * abs(BASE_LONG - zip_long)) ** 2) ** 0.5
			
			#Determine fuel economies
			driver_data['city'].append(fuel_economies['avg_city'])
			driver_data['highway'].append(fuel_economies['avg_highway'])
			driver_data['combined'].append(fuel_economies['avg_combined'])
			
			#Add distance and zipcode
			driver_data['distance'].append(distance)
			driver_data['zipcode'].append(row['zipcode'])
			
			#Add Status
			driver_data['status'].append(filter(str.isalnum, row['status']).upper())
		except:
			#If zipcode not found skip
			status = filter(str.isalnum, row['status']).upper()
			if "PART" in status:
				part_time_skipped = part_time_skipped + 1
			else:
				full_time_skipped = full_time_skipped + 1


#Write to csv file in case someone wants to look at raw data
with open('output_csvs/med_employee.csv', 'w') as csvfile:
	writer = csv.DictWriter(csvfile, fieldnames = ['status', 'zipcode', 'distance', 'city', 'highway', 'combined'])
	for i in range(0, len(driver_data['status'])):
		writer.writerow({
			'status':driver_data['status'][i],
			'zipcode':driver_data['zipcode'][i],
			'distance':driver_data['distance'][i],
			'city':driver_data['city'][i],
			'highway':driver_data['highway'][i],
			'combined':driver_data['combined'][i]
		})


#Caclulate summary
#Fuel economy values are same as crc, already calculated
#Average distance traveled per trip of all Med drivers
distances = {}
#Sums
distances['sum'] = float(sum(driver_data['distance']))
#Average distance traveled per trip of CRC drivers with part time employment status
distances['sum_part_time'] = float(sum([distance for i, distance in enumerate(driver_data['distance']) if "PART" in driver_data['status'][i]]))
#Average distance travel per trip of CRC drivers with full time employement status
distances['sum_full_time'] = float(sum([distance for i, distance in enumerate(driver_data['distance']) if "PART" not in driver_data['status'][i]]))

#Averages
distances['avg'] = float(sum(driver_data['distance']))/float(len(driver_data['distance']))
#Average distance traveled per trip of CRC drivers with part time employment status
distances['avg_part_time'] = float(sum([distance for i, distance in enumerate(driver_data['distance']) if "PART" in driver_data['status'][i]])) / float(len([distance for i, distance in enumerate(driver_data['distance']) if "PART" in driver_data['status'][i]]))
#Average distance travel per trip of CRC drivers with full time employement status
distances['avg_full_time'] = float(sum([distance for i, distance in enumerate(driver_data['distance']) if "PART" not in driver_data['status'][i]])) / float(len([distance for i, distance in enumerate(driver_data['distance']) if "PART" not in driver_data['status'][i]])) 


#Metrics
metrics = {}
metrics['city_10'] = 0 #highest co2 estimate, assume 10 trips/week with city millage
metrics['highway_10'] = 0 #10 trips per week with highway millage
metrics['combined_10'] = 0 #10 trips/week with combined millage
metrics['city_6'] = 0 #6 trips/week with city millage
metrics['highway_6'] = 0 #lowest co2 estimate, 6 trips per week with highway millage
metrics['combined_6'] = 0 #6 trips per week with combined millage
metrics['best_guess'] = 0 #best estimate, uses combined fe, 6 trips/week if employee has part time status, 10 trips/week if full time

#Populate metrics
for i, status in enumerate(driver_data['status']):
	metrics['city_10'] = metrics['city_10'] + (10 * driver_data['distance'][i]/driver_data['city'][i]) * CO2_per_gallon
	metrics['highway_10'] = metrics['highway_10'] + (10 * driver_data['distance'][i]/driver_data['highway'][i]) * CO2_per_gallon
	metrics['city_6'] = metrics['city_6'] + (6 * driver_data['distance'][i]/driver_data['city'][i]) * CO2_per_gallon
	metrics['highway_6'] = metrics['highway_6'] + (6 * driver_data['distance'][i]/driver_data['highway'][i]) * CO2_per_gallon
	metrics['combined_10'] = metrics['combined_10'] + (10 * driver_data['distance'][i]/driver_data['combined'][i]) * CO2_per_gallon
	metrics['combined_6'] = metrics['combined_6'] + (6 * driver_data['distance'][i]/driver_data['combined'][i]) * CO2_per_gallon
	if "PART" in status:
		#If part time assume 6 trips per week
		metrics['best_guess'] = metrics['best_guess'] + (6 * driver_data['distance'][i]/driver_data['combined'][i]) * CO2_per_gallon
	else:
		#If full time assume 10 trips per week
		metrics['best_guess'] = metrics['best_guess'] + (10 * driver_data['distance'][i]/driver_data['combined'][i]) * CO2_per_gallon

#Distance Mins
distances['max'] = max(driver_data['distance']) #Used for debugging not calculations
distances['max_part_time'] = max([distance for i, distance in enumerate(driver_data['distance']) if "PART" in driver_data['status'][i]])
distances['max_full_time'] = max([distance for i, distance in enumerate(driver_data['distance']) if "PART" not in driver_data['status'][i]])

#Upper Error
upper_error = {}
upper_error['best_guess'] = metrics['best_guess'] + (6 * distances['max_part_time']/fuel_economies['max_combined'] * part_time_skipped + 10 * distances['max_full_time']/fuel_economies['max_combined'] * full_time_skipped) * CO2_per_gallon
upper_error['city_10'] = metrics['city_10'] + 10 * distances['max']/fuel_economies['max_city'] * (part_time_skipped + full_time_skipped) * CO2_per_gallon
upper_error['combined_10'] = metrics['combined_10'] + 10 * distances['max']/fuel_economies['max_combined'] * (part_time_skipped + full_time_skipped) * CO2_per_gallon
upper_error['highway_10'] = metrics['highway_10'] + 10 * distances['max']/fuel_economies['max_highway'] * (part_time_skipped + full_time_skipped) * CO2_per_gallon
upper_error['city_6'] = metrics['city_6'] + 6 * distances['max']/fuel_economies['max_city'] * (part_time_skipped + full_time_skipped) * CO2_per_gallon
upper_error['combined_6'] = metrics['combined_6'] + 6 * distances['max']/fuel_economies['max_combined'] * (part_time_skipped + full_time_skipped) * CO2_per_gallon
upper_error['highway_6'] = metrics['highway_6'] + 6 * distances['max']/fuel_economies['max_highway'] * (part_time_skipped + full_time_skipped) * CO2_per_gallon
 
#Distance mins
distances['min'] = min(driver_data['distance'])
distances['min_part_time'] = min([distance for i, distance in enumerate(driver_data['distance']) if "PART" in driver_data['status'][i]])
distances['min_full_time'] = min([distance for i, distance in enumerate(driver_data['distance']) if "PART" not in driver_data['status'][i]])

#Lower Error
lower_error = {}
lower_error['best_guess'] = metrics['best_guess'] + (6 * distances['min_part_time']/fuel_economies['min_combined'] * part_time_skipped + 10 * distances['min_full_time']/fuel_economies['min_combined'] * full_time_skipped) * CO2_per_gallon
lower_error['city_10'] = metrics['city_10'] + 10 * distances['min']/fuel_economies['min_city'] * (part_time_skipped + full_time_skipped) * CO2_per_gallon
lower_error['combined_10'] = metrics['combined_10'] + 10 * distances['min']/fuel_economies['min_combined'] * (part_time_skipped + full_time_skipped) * CO2_per_gallon
lower_error['highway_10'] = metrics['highway_10'] + 10 * distances['min']/fuel_economies['min_highway'] * (part_time_skipped + full_time_skipped) * CO2_per_gallon
lower_error['city_6'] = metrics['city_6'] + 6 * distances['min']/fuel_economies['min_city'] * (part_time_skipped + full_time_skipped) * CO2_per_gallon
lower_error['combined_6'] = metrics['combined_6'] + 6 * distances['min']/fuel_economies['min_combined'] * (part_time_skipped + full_time_skipped) * CO2_per_gallon
lower_error['highway_6'] = metrics['highway_6'] + 6 * distances['min']/fuel_economies['min_highway'] * (part_time_skipped + full_time_skipped) * CO2_per_gallon

#the metric is going to be the value calculated in above for loop plus the average of fe * distance * #skipped
metrics['best_guess'] = metrics['best_guess'] + (6 * distances['avg_part_time']/fuel_economies['avg_combined'] * part_time_skipped + 10 * distances['avg_full_time']/fuel_economies['avg_combined'] * full_time_skipped) * CO2_per_gallon
metrics['city_10'] = metrics['city_10'] + 10 * distances['avg']/fuel_economies['avg_city'] * (part_time_skipped + full_time_skipped) * CO2_per_gallon
metrics['highway_10'] = metrics['highway_10'] + 10 * distances['avg']/fuel_economies['avg_highway'] * (part_time_skipped + full_time_skipped) * CO2_per_gallon
metrics['city_6'] = metrics['city_6'] + 6 * distances['avg']/fuel_economies['avg_city'] * (part_time_skipped + full_time_skipped) * CO2_per_gallon
metrics['highway_6'] = metrics['highway_6'] + 6 * distances['avg']/fuel_economies['avg_highway'] * (part_time_skipped + full_time_skipped) * CO2_per_gallon
metrics['combined_10'] = metrics['combined_10'] + 10 * distances['avg']/fuel_economies['avg_combined'] * (part_time_skipped + full_time_skipped) * CO2_per_gallon
metrics['combined_6'] = metrics['combined_6'] + 6 * distances['avg']/fuel_economies['avg_combined'] * (part_time_skipped + full_time_skipped) * CO2_per_gallon

#Print Summary Data
print "Med Summary Data"
print "Total {}, full time skipped {}, part time skipped {}".format(total, full_time_skipped, part_time_skipped)
for key, value in metrics.iteritems():
	print "metric {}: lower limit {}, metric {}, higher limit {}".format(key, lower_error[key], value, upper_error[key])
for key, value in distances.iteritems():
	print "distance {}: {}".format(key, value)  


with open("graph_data.csv", "a") as csvfile:
	writer = csv.DictWriter(csvfile, fieldnames=['group', 'lower_error', 'metric', 'upper_error'])
	writer.writerow({'group':'med_employee', 'lower_error':lower_error['best_guess'], 'metric':metrics['best_guess'], 'upper_error':upper_error['best_guess']})
