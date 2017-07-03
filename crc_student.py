from fuzzywuzzy import fuzz
import csv
from glob import glob

RIDES = 10 #Might change this -> since reading in part-time/full-time status
employee_skipped = 0
student_skipped = 0

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



#Read in Zipcode data
zipcodes = {'zipcode':[], 'lat':[], 'long':[]}

with open('zip_code_database.csv') as csvfile:
	reader = csv.DictReader(csvfile, fieldnames=['zipcode', 'lat', 'long'])
	for row in reader:
		#print row['zipcode']
		zipcodes['zipcode'].append(row['zipcode'])
		zipcodes['lat'].append(float(row['lat']))
		zipcodes['long'].append(float(row['long']))


#Read in CRC Employee Data
crc_employee_driver_data = {'zipcode':[], 'make-model':[], 'year':[], 'status':[], 'distance':[]}

#Lat and long of Charles River Campus
BASE_LAT = 42.35
BASE_LONG = -71.11

with open('CRCEmployeePermit.csv') as csvfile:
	reader = csv.DictReader(csvfile, fieldnames=['make', 'model', 'year', 'zipcode', 'status'])
	for row in reader:
		try:
			zip_lat = zipcodes['lat'][zipcodes['zipcode'].index(row['zipcode'])]
			zip_long = zipcodes['long'][zipcodes['zipcode'].index(row['zipcode'])]
			distance = RIDES * ((69 * abs(BASE_LAT - zip_lat)) ** 2 + (51 * abs(BASE_LONG - zip_long)) ** 2) ** 0.5
		
			crc_employee_driver_data['distance'].append(distance) 
			crc_employee_driver_data['zipcode'].append(row['zipcode'])
		
			make_model = "{}{}".format(row['make'], row['model'])
			make_model = make_model.replace("+AC0", "")
			make_model = filter(str.isalnum, make_model)
			make_model = make_model.upper()
		
			crc_employee_driver_data['make-model'].append(make_model)
		
			crc_employee_driver_data['year'].append(row['year'])
			crc_employee_driver_data['status'].append(row['status'])
		except:
			employee_skipped = employee_skipped + 1
			#print "skipped: {}".format(row['zipcode'])


#Match EPA data to CRC Driver data
crc_employee_fuel_data = {'zipcode':[], 'make-model':[], 'year':[], 'status':[], 'distance':[], 'city':[], 'highway':[], 'combined':[]} 

for i in range(0, len(crc_employee_driver_data['status'])):
	try:	
		year_matches = [j for j, x in enumerate(epa_data['year']) if x == crc_employee_driver_data['year'][i]]
		indecies = []
		ratios = []
		for year_match in year_matches:
			ratio = fuzz.ratio(epa_data['make-model'][year_match], crc_employee_driver_data['make-model'][i])
			if ratio > 80:
				ratios.append(ratio)
				indecies.append(year_match)
		index = indecies[ratios.index(max(ratios))]
		
		crc_employee_fuel_data['city'].append(float(epa_data['city'][index]))
		crc_employee_fuel_data['highway'].append(float(epa_data['highway'][index]))
		crc_employee_fuel_data['combined'].append(float(epa_data['combined'][index]))
		
		crc_employee_fuel_data['status'].append(crc_employee_driver_data['status'][i])	
		crc_employee_fuel_data['zipcode'].append(crc_employee_driver_data['zipcode'][i])	
		crc_employee_fuel_data['distance'].append(crc_employee_driver_data['distance'][i])	
		crc_employee_fuel_data['year'].append(crc_employee_driver_data['year'][i])
		crc_employee_fuel_data['make-model'].append(crc_employee_driver_data['make-model'][i])
		#print "found: {} {}".format(crc_employee_driver_data['make-model'][i], crc_employee_driver_data['year'][i])
	except:
		employee_skipped = employee_skipped + 1
		#print "skipped: {} {}".format(crc_employee_driver_data['make-model'][i], crc_employee_driver_data['year'][i])


#Write out formated CSV
with open('crc_employee.csv', 'w') as csvfile:
	writer = csv.DictWriter(csvfile, fieldnames=['zipcode', 'make-model', 'year', 'status', 'distance', 'city', 'highway', 'combined'])
	 
	for i in range(0, len(crc_employee_fuel_data['status'])):
		writer.writerow({
			'status':crc_employee_fuel_data['status'][i],
			'zipcode':crc_employee_fuel_data['zipcode'][i],
			'distance':crc_employee_fuel_data['distance'][i],
			'make-model':crc_employee_fuel_data['make-model'][i],
			'year':crc_employee_fuel_data['year'][i],
			'city':crc_employee_fuel_data['city'][i],
			'highway':crc_employee_fuel_data['highway'][i],
			'combined':crc_employee_fuel_data['combined'][i]
		})


#Read in CRC Student data
crc_student_driver_data = {'status':[], 'make-model':[], 'year':[], 'zipcode':[], 'distance':[]}

with open('CRCStudentPermit.csv') as csvfile:
	reader = csv.DictReader(csvfile, fieldnames=['status', 'make', 'model', 'year', 'zipcode'])
	for row in reader:
		try:
			zip_lat = zipcodes['lat'][zipcodes['zipcode'].index(row['zipcode'])]
			zip_long = zipcodes['long'][zipcodes['zipcode'].index(row['zipcode'])]
			distance = RIDES * ((69 * abs(BASE_LAT - zip_lat)) ** 2 + (51 * abs(BASE_LONG - zip_long)) ** 2) ** 0.5
		
			crc_student_driver_data['distance'].append(distance) 
			
			make_model = "{}{}".format(row['make'], row['model'])
			make_model = make_model.replace("+AC0", "")
			make_model = filter(str.isalnum, make_model)
			make_model = make_model.upper()
		
			crc_student_driver_data['make-model'].append(make_model)
		
			crc_student_driver_data['status'].append(row['status'])
			crc_student_driver_data['year'].append(row['year'])
			crc_student_driver_data['zipcode'].append(row['zipcode'])
		except:
			student_skipped = student_skipped + 1
			#print "skipped: {}".format(row['zipcode'])


#Match EPA Data to student Driver Data
crc_student_fuel_data = {'zipcode':[], 'make-model':[], 'year':[], 'status':[], 'distance':[], 'city':[], 'highway':[], 'combined':[]} 

for i in range(0, len(crc_student_driver_data['status'])):
	try:	
		year_matches = [j for j, x in enumerate(epa_data['year']) if x == crc_student_driver_data['year'][i]]
		indecies = []
		ratios = []
		for year_match in year_matches:
			ratio = fuzz.ratio(epa_data['make-model'][year_match], crc_student_driver_data['make-model'][i])
			if ratio > 80:
				ratios.append(ratio)
				indecies.append(year_match)
		index = indecies[ratios.index(max(ratios))]
		
		crc_student_fuel_data['city'].append(float(epa_data['city'][index]))
		crc_student_fuel_data['highway'].append(float(epa_data['highway'][index]))
		crc_student_fuel_data['combined'].append(float(epa_data['combined'][index]))
		
		crc_student_fuel_data['status'].append(crc_student_driver_data['status'][i])	
		crc_student_fuel_data['zipcode'].append(crc_student_driver_data['zipcode'][i])	
		crc_student_fuel_data['distance'].append(crc_student_driver_data['distance'][i])	
		crc_student_fuel_data['year'].append(crc_student_driver_data['year'][i])
		crc_student_fuel_data['make-model'].append(crc_student_driver_data['make-model'][i])
		#print "found: {} {}".format(crc_employee_driver_data['make-model'][i], crc_employee_driver_data['year'][i])
	except:
		student_skipped = student_skipped + 1
		#print "skipped: {} {}".format(crc_student_driver_data['make-model'][i], crc_student_driver_data['year'][i])


#Write out formated CSV
with open('crc_student.csv', 'w') as csvfile:
	writer = csv.DictWriter(csvfile, fieldnames=['zipcode', 'make-model', 'year', 'status', 'distance', 'city', 'highway', 'combined'])
	 
	for i in range(0, len(crc_student_fuel_data['status'])):
		writer.writerow({
			'status':crc_student_fuel_data['status'][i],
			'zipcode':crc_student_fuel_data['zipcode'][i],
			'distance':crc_student_fuel_data['distance'][i],
			'make-model':crc_student_fuel_data['make-model'][i],
			'year':crc_student_fuel_data['year'][i],
			'city':crc_student_fuel_data['city'][i],
			'highway':crc_student_fuel_data['highway'][i],
			'combined':crc_student_fuel_data['combined'][i]
		})


#Read in Medical Campus Employee Data
employee_city_proportion = float(sum(crc_employee_fuel_data['city']))/float(len(crc_employee_fuel_data['city']))
employee_highway_proportion = float(sum(crc_employee_fuel_data['highway']))/float(len(crc_employee_fuel_data['highway']))
employee_combined_proportion = float(sum(crc_employee_fuel_data['combined']))/float(len(crc_employee_fuel_data['combined']))

med_employee_fuel_data = {'status':[], 'zipcode':[], 'distance':[], 'city':[], 'highway':[], 'combined':[]}

#Lat and long of medical campus
BASE_LAT = 42.34 
BASE_LONG = -71.07

with open('MEDEmployeePermit.csv') as csvfile:
	reader = csv.DictReader(csvfile, fieldnames=['zipcode', 'status'])
	for row in reader:
		try:
			zip_lat = zipcodes['lat'][zipcodes['zipcode'].index(row['zipcode'])]
			zip_long = zipcodes['long'][zipcodes['zipcode'].index(row['zipcode'])]
			distance = RIDES * ((69 * abs(BASE_LAT - zip_lat)) ** 2 + (51 * abs(BASE_LONG - zip_long)) ** 2) ** 0.5

			med_employee_fuel_data['distance'].append(distance)
			med_employee_fuel_data['zipcode'].append(row['zipcode'])
			med_employee_fuel_data['status'].append(row['status'])
			med_employee_fuel_data['city'].append(employee_city_proportion)
			med_employee_fuel_data['highway'].append(employee_highway_proportion)
			med_employee_fuel_data['combined'].append(employee_combined_proportion)
		except:
			employee_skipped = employee_skipped + 1
			#print "skipped: {}".format(row['zipcode'])

#Write to csv file
with open('med_employee.csv', 'w') as csvfile:
	writer = csv.DictWriter(csvfile, fieldnames = ['status', 'zipcode', 'distance', 'city', 'highway', 'combined'])
	
	for i in range(0, len(med_employee_fuel_data['status'])):
		writer.writerow({
			'status':med_employee_fuel_data['status'][i],
			'zipcode':med_employee_fuel_data['zipcode'][i],
			'distance':med_employee_fuel_data['distance'][i],
			'city':med_employee_fuel_data['city'][i],
			'highway':med_employee_fuel_data['highway'][i],
			'combined':med_employee_fuel_data['combined'][i]
		})
	


#Read in Medical Campus Student Data
student_city_proportion = float(sum(crc_student_fuel_data['city']))/float(len(crc_student_fuel_data['city']))
student_highway_proportion = float(sum(crc_student_fuel_data['highway']))/float(len(crc_student_fuel_data['highway']))
student_combined_proportion = float(sum(crc_student_fuel_data['combined']))/float(len(crc_student_fuel_data['combined']))

med_student_fuel_data = {'status':[], 'zipcode':[], 'distance':[], 'city':[], 'highway':[], 'combined':[]}

with open('MEDStudentPermit.csv') as csvfile:
	reader = csv.DictReader(csvfile, fieldnames=['zipcode', 'status'])
	for row in reader:
		try:
			zip_lat = zipcodes['lat'][zipcodes['zipcode'].index(row['zipcode'])]
			zip_long = zipcodes['long'][zipcodes['zipcode'].index(row['zipcode'])]
			distance = RIDES * ((69 * abs(BASE_LAT - zip_lat)) ** 2 + (51 * abs(BASE_LONG - zip_long)) ** 2) ** 0.5

			med_student_fuel_data['distance'].append(distance)
			med_student_fuel_data['zipcode'].append(row['zipcode'])
			med_student_fuel_data['status'].append(row['status'])
			med_student_fuel_data['city'].append(student_city_proportion)
			med_student_fuel_data['highway'].append(student_highway_proportion)
			med_student_fuel_data['combined'].append(student_combined_proportion)
		except:
			student_skipped = student_skipped + 1
			#print "skipped: {}".format(row['zipcode'])

#Write to csv file
with open('med_student.csv', 'w') as csvfile:
	writer = csv.DictWriter(csvfile, fieldnames = ['status', 'zipcode', 'distance', 'city', 'highway', 'combined'])
	
	for i in range(0, len(med_student_fuel_data['status'])):
		writer.writerow({
			'status':med_student_fuel_data['status'][i],
			'zipcode':med_student_fuel_data['zipcode'][i],
			'distance':med_student_fuel_data['distance'][i],
			'city':med_student_fuel_data['city'][i],
			'highway':med_student_fuel_data['highway'][i],
			'combined':med_student_fuel_data['combined'][i]
		})


#Summary
#Print out number of lbs of CO2 produced
#CRC Employees
crc_employee_co2 = 0
for i, d in enumerate(crc_employee_fuel_data['distance']):
	crc_employee_co2 = crc_employee_co2 + 20 * d * crc_employee_fuel_data['city'][i]
print "crc employee co2 production: {} lb".format(crc_employee_co2) 

#CRC Students
crc_student_co2 = 0
for i, d in enumerate(crc_student_fuel_data['distance']):
	crc_student_co2 = crc_student_co2 + 20 * d * crc_student_fuel_data['city'][i]
print "crc student co2 production: {} lb".format(crc_student_co2) 

#Med Employee
med_employee_co2 = 0
for i, d in enumerate(med_employee_fuel_data['distance']):
	med_employee_co2 = med_employee_co2 + 20 * d * med_employee_fuel_data['city'][i]
print "med employee co2 production: {} lb".format(med_employee_co2) 

#Med Students
med_student_co2 = 0
for i, d in enumerate(med_student_fuel_data['distance']):
	med_student_co2 = med_student_co2 + 20 * d * med_student_fuel_data['city'][i]
print "med student co2 production: {} lb".format(med_student_co2) 

#Determine number of student and employee cars that were not included in calculation due to bad zipcode or unfound car data
part_student_skipped = float(student_skipped)/(float(len(med_student_fuel_data['status'])) + float(len(crc_student_fuel_data['status'])) + float(student_skipped))
print "part student skipped: {}".format(part_student_skipped)


part_employee_skipped = float(employee_skipped)/(float(len(med_employee_fuel_data['status'])) + float(len(crc_employee_fuel_data['status'])) + float(employee_skipped))
print "part employee skipped: {}".format(part_employee_skipped)

