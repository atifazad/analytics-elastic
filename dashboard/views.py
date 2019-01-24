from django.shortcuts import render
from services.fetchdata import FetchData
from pprint import pprint
import json
from datetime import datetime

from django.views.decorators.clickjacking import xframe_options_exempt

#Index page
def index(request):
	return render(request, 'dashboard.html', {
		'review_metrics_dataset': json.dumps(get_review_metrics(request)),
		'average_rating_over_time_dataset': json.dumps(get_average_rating_over_time_dataset(request)),
		'rating_breakdown_dataset': json.dumps(get_rating_breakdown_dataset(request)),
		'nps_breakdown_dataset': json.dumps(get_nps_breakdown_dataset(request)),
		'reviews_timeline': json.dumps(get_reviews_timeline(request))
		})

#Widget page
@xframe_options_exempt
def widget(request):
	return render(request, 'widget.html', {
		'average_rating_over_time_dataset': json.dumps(get_average_rating_over_time_dataset(request))
	})

#Widget2 page
@xframe_options_exempt
def widget2(request):
	return render(request, 'widget2.html', {
		'nps_breakdown_dataset': json.dumps(get_nps_breakdown_dataset(request))
	})

def get_review_metrics(request):

	options = {}
	options["metafilters"] = request.GET.get("metafilters", '[]')

	fetch = FetchData()
	results = fetch.search('review_metrics', options)

	count = results['hits']['total']
	average_rating = results['aggregations']['avg_rating']['value']

	dataset = {
		"review_count": count,
		"average_rating": average_rating
	}

	return dataset

def get_average_rating_over_time_dataset(request):

	options = {}
	options["metafilters"] = request.GET.get("metafilters", '[]')

	fetch = FetchData()

	options['interval']='1y'
	results = fetch.search('average_rating_over_time', options)

	buckets = results['aggregations']['reviews_over_time']['buckets']

	yearly_dataset=[]
	for entry in buckets:
		datapoint = [ entry.get('key') , entry['average_rating']["value"] ]
		yearly_dataset.append(datapoint)

	options['interval']='1M'
	results = fetch.search('average_rating_over_time', options)

	buckets = results['aggregations']['reviews_over_time']['buckets']

	monthly_dataset=[]
	for entry in buckets:
		datapoint = [ entry.get('key') , entry['average_rating']["value"] ]
		monthly_dataset.append(datapoint)

	options['interval']='1D'
	results = fetch.search('average_rating_over_time', options)

	buckets = results['aggregations']['reviews_over_time']['buckets']

	daily_dataset=[]
	for entry in buckets:
		datapoint = [ entry.get('key') , entry['average_rating']["value"] ]
		daily_dataset.append(datapoint)

	dataset = {
		'yearly_dataset': yearly_dataset,
		'monthly_dataset': monthly_dataset,
		'daily_dataset': daily_dataset
	}

	return dataset

def get_rating_breakdown_dataset(request):

	options = {}
	options["metafilters"] = request.GET.get("metafilters", '[]')

	fetch = FetchData()
	results = fetch.search('rating_breakdown', options)

	total = results['hits']['total']

	buckets = results['aggregations']['sentiments_breakdown']['buckets']

	sentiments=[]
	ratings=[]
	colors = {
		"sentiments": {
			"Positive": "LightGreen",
			"Neutral": "Yellow",
			"Negative": "Red"
		},
		"ratings": {
			1: "Red",
			2: "Red",
			3: "Yellow",
			4: "LightGreen",
			5: "LightGreen",
		}
	}
	for entry in buckets:
		datapoint = {
			'name': entry['key'],
			'data': [ entry['doc_count'] ],
			'color': colors["sentiments"][entry['key']]
		} 
		sentiments.append(datapoint)

		rating_buckets = entry['rating_breakdown']['buckets']
		for rating_entry in rating_buckets:
			datapoint = {
				'rating': rating_entry.get('key'),
				'y': rating_entry.get('doc_count'),
				'percentage': rating_entry['doc_count'] / total * 100,
				'color': colors["ratings"][rating_entry['key']]
			} 
			ratings.append(datapoint)

	dataset = {
		'total':total,
		'sentiments':sentiments,
		'ratings':ratings
	}

	return dataset

def get_nps_breakdown_dataset(request):

	options = {}
	options["metafilters"] = request.GET.get("metafilters", '[]')

	fetch = FetchData()
	q_results = fetch.search('nps_questions')
	result_hits = q_results["hits"]["hits"]
	question_ids = []

	for hit in result_hits:
		q_id = hit["_source"]["external_id"]
		question_ids.append(q_id)

	options['question_ids'] = question_ids

	breakdown_results = fetch.search('nps_breakdown', options=options)

	total = breakdown_results['hits']['total']

	buckets = breakdown_results['aggregations']['sentiments_breakdown']['buckets']

	sentiments=[]
	scores=[]
	nps_metrics={}
	colors = {
		"sentiments": {
			"Promoter": "LightGreen",
			"Passive": "Yellow",
			"Detractor": "Red"
		},
		"scores": {
			0: "Red",
			1: "Red",
			2: "Red",
			3: "Red",
			4: "Red",
			5: "Red",
			6: "Red",
			7: "Yellow",
			8: "Yellow",
			9: "LightGreen",
			10: "LightGreen"
		}
	}
	for entry in buckets:

		#Datapoints for NPS sentiment breakdown
		datapoint = {
			'name': entry['key'],
			'data': [ entry['doc_count'] ],
			'color': colors["sentiments"][entry['key']]
		}
		sentiments.append(datapoint)

		#NPS metrics
		nps_metrics[entry['key']] = entry['doc_count']

		#Datapoints for NPS score breakdown
		score_buckets = entry['score_breakdown']['buckets']
		for score_entry in score_buckets:
			datapoint = {
				'score': score_entry.get('key'),
				'y': score_entry.get('doc_count'),
				'percentage': score_entry['doc_count'] / total * 100,
				'color': colors["scores"][score_entry['key']]
			} 
			scores.append(datapoint)

	pprint(nps_metrics)

	nps_metrics['nps_score'] = 0
	if total > 0:
		nps_metrics['nps_score'] = round((nps_metrics.get('Promoter', 0) * 100 / total)) - round((nps_metrics.get('Detractor', 0) * 100 / total))
	nps_metrics['total_nps_answers'] = total

	dataset = {
		'total':total,
		'sentiments':sentiments,
		'scores':scores,
		'nps_metrics': nps_metrics
	}

	return dataset

def get_reviews_timeline(request):

	options = {}
	options["metafilters"] = request.GET.get("metafilters", '[]')

	fetch = FetchData()
	results = fetch.search('review_timeline', options)

	total = results['hits']['total']

	buckets = results['aggregations']['rating_breakdown']['buckets']

	dataset = {}

	rating_datalist=[]
	drilldown_list=[]
	for entry in buckets:
		rating_dict = {}
		rating = int(entry['key'])
		rating_dict['name'] = rating

		yearly_buckets = entry['yearly_stats']['buckets']

		year_datalist = []
		for yearly_entry in yearly_buckets:
			year_data={}
			year = datetime.utcfromtimestamp(yearly_entry['key']/1000).year
			year_data['name'] = year
			year_data['y'] = yearly_entry['doc_count']
			year_data['drilldown'] = str(rating) + '-months-' + str(year)

			year_datalist.append(year_data)


			monthly_buckets = yearly_entry['monthly_stats']['buckets']

			day_drilldown = []
			month_drilldown_dict = {}
			month_drilldown_dict['id'] = str(rating) + '-months-' + str(year)
			month_drilldown_dict['name'] = rating
			month_drilldown_list = []
			for monthly_entry in monthly_buckets:
				month_data={}
				month = datetime.utcfromtimestamp(monthly_entry['key']/1000).strftime("%B") + ' ' + str(year)
				month_data['name'] = month
				month_data['y'] = monthly_entry['doc_count']
				month_data['drilldown'] = 'days-' + str(rating) + '-' + month
				month_drilldown_list.append(month_data)

				daily_buckets = monthly_entry['daily_stats']['buckets']


				day_drilldown_dict = {}
				day_drilldown_dict['id'] = 'days-' + str(rating) + '-' + month
				day_drilldown_dict['name'] = rating
				day_drilldown_list = []
				for day_entry in daily_buckets:
					day_data={}
					day = datetime.utcfromtimestamp(day_entry['key']/1000).strftime('%d-%b-%Y')
					day_data['name'] = day
					day_data['y'] = day_entry['doc_count']

					day_drilldown_list.append(day_data)

				day_drilldown_dict['data'] = day_drilldown_list
				drilldown_list.append(day_drilldown_dict)

			month_drilldown_dict['data'] = month_drilldown_list
			drilldown_list.append(month_drilldown_dict)

		rating_dict['data'] = year_datalist
		rating_datalist.append(rating_dict)

	dataset = {
		'main_dataset': rating_datalist,
		'drilldown_dataset': drilldown_list
	}

	return dataset


