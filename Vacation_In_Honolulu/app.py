#################################################
# FLASK API
#################################################

#################################################
# Import the dependencies.
#################################################
import datetime as dt
from datetime import timedelta

from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, func

from flask import Flask, jsonify
#################################################


#################################################
# Database Setup
#################################################
engine = create_engine("sqlite:///Resources/hawaii.sqlite")

# reflect an existing database into a new model
Base = automap_base()

# reflect the tables
Base.prepare(autoload_with = engine)

# Save references to each table
Measurement = Base.classes.measurement
Station = Base.classes.station


#################################################
# Flask Setup
#################################################
app = Flask(__name__)


#####################################################
# Common Functions
#####################################################

# return the 12 month previous date from a given date
def past_year_date(date):
    # return date - 12 months
    return date - dt.timedelta(days=365)


# Return most recent date in the database
def most_recent_date(session):
    # Get the one year ago date using the most recent date recorded in the database
    most_recent_date_row = session.query(Measurement.date).\
                            order_by(Measurement.date.desc()).first()

    return dt.datetime.strptime(most_recent_date_row[0], '%Y-%m-%d')


# Calculate TMIN, TAVG, and TMAX from start and end(optional) date(s) 
# Return in JSON format
def start_end_dates(start, end=None):
    session = Session(engine) 

    # IF end is None than end = most recent date
    if end == None:
        end = most_recent_date(session)

    # Query the min, average, and max tobs greater than or equal to the URL date
    date_results = session.query(func.min(Measurement.tobs),
                                 func.avg(Measurement.tobs),
                                 func.max(Measurement.tobs)).\
                                 filter(Measurement.date >= start).\
                                 filter(Measurement.date <= end).all()
    session.close() 

    # MIN, MAX, AVERAGE list
    temperature_results = []

    for min, avg, max in date_results:
        # dictionary to append
        info = {'Temperature MIN':min,
                'Temperature MAX':max,
                'Temperature AVG':avg}
        
        # append dictionary to list
        temperature_results.append(info)
    
    # result
    return jsonify(temperature_results)
#################################################

#################################################
# Flask Routes
#################################################
@app.route("/")
def welcome():
    """List all available api routes."""
    return (
        f"<b>Date Format Example: 2017-05-08</b><br/>"
        f"<br/>"
        f"<b>Available Routes:</b><br/>"
        f"/api/v1.0/precipitation<br/>"
        f"/api/v1.0/stations<br/>"
        f"/api/v1.0/tobs<br/>"
        f"/api/v1.0/&ltstart date&gt<br/>"
        f"/api/v1.0/&ltstart date&gt/&ltend date&gt"
    )
#################################################


############################################################################################################
# Convert the query results from your precipitation analysis (i.e. retrieve only the last 12 months of data) 
# to a dictionary using date as the key and prcp as the value.
############################################################################################################
@app.route("/api/v1.0/precipitation")
def precipitation():
    # Create session 
    session = Session(engine)

    # Get the one year ago date using the most recent date recorded in the database
    one_year_ago = past_year_date(most_recent_date(session))

    # Query one year precipitation and dates
    results = session.query(Measurement.date,Measurement.prcp).\
        order_by(Measurement.date.desc()).filter(Measurement.date > one_year_ago)

    session.close()

    # Create a dictionary result
    precipitation_dict = {}
    for date,prcp in results:
        if prcp != None :
            precipitation_dict[date] = prcp

    return jsonify(precipitation_dict)
##################################################


##################################################
# Return a JSON list of stations from the dataset.
##################################################
@app.route("/api/v1.0/stations")
def stations():
    # Create session 
    session = Session(engine)

    # Query stations
    results = session.query(Station.id,
                            Station.station,
                            Station.name,
                            Station.latitude,
                            Station.longitude,
                            Station.elevation).all()
    session.close()

    # List of stations
    stations=[]

    # populate list of stations
    for station in results:
        # dictionary to append
        info = {'ID':station[0],
            'Station':station[1],
            'Name':station[2],
            'Latitude':station[3],
            'Longitude':station[4],
            'Elevation':station[5]}
        
        # append dictionary to list
        stations.append(info)

    # result
    return jsonify(stations)
#######################################################################################################


#######################################################################################################
# Query the dates and temperature observations of the most-active station for the previous year of data
# Return a JSON list of temperature observations for the previous year
#######################################################################################################
@app.route("/api/v1.0/tobs")
def date_and_temp():
    # Create session
    session = Session(engine)

    # Get the one year ago date using the most recent date recorded in the database
    one_year_ago = past_year_date(most_recent_date(session))

    # get the most active station 
    station_activity = session.query(Measurement.station,func.count(Measurement.station)).\
            group_by(Measurement.station).\
            order_by(func.count(Measurement.station).desc()).first() 
    
    # extract the value
    top_station_number = station_activity[0]

    # Query the dates and temperature
    results = session.query(Measurement.station, Measurement.date, Measurement.tobs).\
            order_by(Measurement.date.desc()).\
            filter(Measurement.date > one_year_ago).\
            filter(Measurement.station == top_station_number)
    
    session.close()

    # Date and Temperature list
    temp_observations = []

    for stat, date, tobs in results:
        # dictionary to append
        obs_dict = {'Station':stat,
                    'Date':date,
                    'Temperature':tobs}
        
        # append dictionary to list
        temp_observations.append(obs_dict)

    # result
    return jsonify(temp_observations)
################################################################################################################


#################################################################################################################
# For a specified start, calculate TMIN, TAVG, and TMAX for all the dates greater than or equal to the start date
#################################################################################################################
@app.route("/api/v1.0/<start>")
def start_date(start):
    return start_end_dates(start, None)
####################################################################


####################################################################
# For a specified start and end date, calculate TMIN, TAVG, and TMAX 
####################################################################
@app.route("/api/v1.0/<start>/<end>")
def start_end_date(start, end):
    return start_end_dates(start, end)
########################################


########################################
# RUN FLASK
########################################
if __name__ == '__main__':
    app.run(debug=True)
