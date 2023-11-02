
import requests
import json

app_name = 'ai_test'
api_key = 'x44qHcqfmH76HiU7i4d3F3yt'
secret_key = 'SRYYDN0j5pLL6qgFq8Nq97NU4XXK3HCG'
def main():
        
    url = "https://aip.baidubce.com/oauth/2.0/token?grant_type=client_credentials&client_id=x44qHcqfmH76HiU7i4d3F3yt&client_secret=SRYYDN0j5pLL6qgFq8Nq97NU4XXK3HCG"
    print('url', url)
    payload = ""
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }
    
    response = requests.request("POST", url, headers=headers, data=payload)
    
    print(response.text)
    

if __name__ == '__main__':
    main()