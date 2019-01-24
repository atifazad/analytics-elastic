from elasticsearch import Elasticsearch
from pprint import pprint
import json
import requests

class FetchData() :

	def get_query_of_type(self, type):
		options = {
			'review_metrics': { 
				"query": self.get_review_metrics,
				"index": "*_reviews"
			},
			'average_rating_over_time' : { 
				"query": self.get_average_rating_over_time,
				"index": "*_reviews"
			},
			'rating_breakdown' : { 
				"query": self.get_rating_breakdown,
				"index": "*_reviews"
			},
			'nps_questions' : { 
				"query": self.get_nps_questions,
				"index": "*_questions"
			},
			'nps_breakdown': {
				"query": self.get_nps_breakdown,
				"index": "*_answers"
			},
			'review_timeline': {
				"query": self.get_reviews_timeline,
				"index": "*_reviews"
			}
		}

		return options[type]

	def get_metafilters_array(self, options):
		
		filter_array=[]

		if options.get('metafilters', None) != None:
			metafilters=json.loads(options['metafilters'])
			# pprint (metafilters)
			for afilter in metafilters:
				filter_dict = {
					"match": {
						"recipient_metadata." + afilter["key"]:afilter["value"]
					}
				}

				filter_array.append(filter_dict)

		return filter_array

	def get_review_metrics(self, options=None):

		filter_array = []

		body = {
			"_source":{
			    "includes":"order_id"
			  },
			  "query":{
			  	"exists": {
			  		"field":"rating"
			  	}
			  },
			  "aggs":{
			    "avg_rating": {
			      "avg": {
			        "field":"rating"
			      }
			    }
			  }
	  		}

		if options != None:
			filter_array = self.get_metafilters_array(options)

		filter_array.append ( {
			"exists": {
				"field":"rating"
			}
		})

		body["query"] = {
			"bool": {
				"must":filter_array
			}
		}
		return json.dumps(body)

	def get_average_rating_over_time(self, options=None):

		filter_array = []

		body = {
			"aggs": {
			    "reviews_over_time": {
			      "date_histogram": {
			        "field": "review_time",
			        "interval": options['interval'],
			        "min_doc_count": 0
			      },
			      "aggs": {
			        "average_rating": {
			          "avg": {
			            "field": "rating"
			          }
			        }
			      }
			    }
			  },
			  "size": 0
			}

		if options != None:
			filter_array = self.get_metafilters_array(options)

		filter_array.append ( {
				"exists": {
					"field":"rating"
				}
			})
		body["query"] = {
			"bool": {
				"must":filter_array
			}
		}

		return json.dumps(body)

	def get_rating_breakdown(self, options=None):

		filter_array = []

		body = {
			"aggs": {
			    "sentiments_breakdown": {
			      "terms": {
			        "field": "sentiments_verbose.keyword",
			        "size": 5,
			        "order": {
			          "_count": "desc"
			        }
			      },
			      "aggs": {
			        "rating_breakdown": {
			          "histogram": {
			            "field": "rating",
			            "interval": 1,
			            "min_doc_count": 0
			          }
			        }
			      }
			    }
			  },
			  "size": 0
		}

		if options != None:
			filter_array = self.get_metafilters_array(options)

		filter_array.append ( {
				"exists": {
					"field":"rating"
				}
			})
		body["query"] = {
			"bool": {
				"must":filter_array
			}
		}
		
		pprint (body)

		return json.dumps(body)

	def get_nps_questions(self, options=None):

		return json.dumps({
			"_source": {
			    "includes": ["external_id"]
			  },
			  "size": 10000,
			  "query":{
			    "bool":{
			      "must":[
			          {
			            "term":{
			              "options_count":11
			            }
			          },
			          {
			            "term":{
			              "options_min":0
			            }
			          },
			          {
			            "term":{
			              "options_max":10
			            }
			          }
			        ]
			    }
			  }	
			})

	def get_nps_breakdown(self, options=None):

		question_ids = options['question_ids']


		filter_array = []

		body = {
			  "aggs":{
			    "sentiments_breakdown": {
			      "terms": {
			        "field": "sentiment.keyword",
			        "order": {
			          "_count": "desc"
			        }
			      },
			      "aggs": {
			        "score_breakdown": {
			          "histogram": {
			            "field": "answer_value",
			            "interval": 1,
			            "min_doc_count": 0
			          }
			        }
			      }
			    }
			  }
			}

		if options != None:
			filter_array = self.get_metafilters_array(options)

		filter_array.append ( {
			    "terms": {
			      "question_id.keyword": question_ids
			    }
			  })

		body["query"] = {
			"bool": {
				"must":filter_array
			}
		}
		return json.dumps(body)

	def get_reviews_timeline(self, options:None):

		filter_array = []

		body = {
			"size":0,
	  		"query":{
		    "match_all":{}
		  },
		  "aggs":{
		    "rating_breakdown":{
		      "histogram":{
		        "field":"rating",
		        "interval":1,
		        "min_doc_count":0
		      },
		      "aggs":{
		        "yearly_stats":{
		          "date_histogram":{
		            "field":"review_time",
		            "interval":"1y",
		            "min_doc_count":0
		          },
		          "aggs":{
		            "monthly_stats":{
		              "date_histogram":{
		                "field": "review_time",
		                "interval": "1M",
		                "min_doc_count":0
		              },
		              "aggs":{
		                "daily_stats": {
		                  "date_histogram":{
		                    "field": "review_time",
		                    "interval": "1D",
		                    "min_doc_count":0
		                  }
		                }
		              }
		            }
		          }
		        }
		      }
		    }
		  }
		}

		if options != None:
			filter_array = self.get_metafilters_array(options)

		filter_array.append ( {
				"exists": {
					"field":"rating"
				}
			})
		body["query"] = {
			"bool": {
				"must":filter_array
			}
		}

		return json.dumps(body)

	def search(self, type, options=None) :

		es = Elasticsearch([
	    	{'host': 'localhost', 'port': 9200}
		])

		queryConfig = self.get_query_of_type(type)
		query = queryConfig['query'](options)

		uri = 'http://localhost:9200/'+ queryConfig['index'] +'/_doc/_search'
		headers = {'Content-Type': 'application/json'}

		response = requests.get(uri, data=query, headers=headers)
		results = json.loads(response.text)

		return results;
