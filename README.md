# Traffic Monitor
**Visit the website at:** [https://traffic-monitor.pages.dev](https://traffic-monitor.pages.dev)

<!--Badges-->
![Google Cloud](https://img.shields.io/badge/Google%20Cloud-%234285F4.svg?style=for-the-badge&logo=google-cloud&logoColor=white) &nbsp; &nbsp; &nbsp; 
![AWS](https://img.shields.io/badge/AWS-orange?style=for-the-badge&logo=amazonwebservices&logoSize=auto) &nbsp; &nbsp; &nbsp;
![Cloudflare](https://img.shields.io/badge/Cloudflare-F38020?style=for-the-badge&logo=Cloudflare&logoColor=white) &nbsp; &nbsp; &nbsp;
![React](https://img.shields.io/badge/react-%2320232a.svg?style=for-the-badge&logo=react&logoColor=%2361DAFB) &nbsp; &nbsp; &nbsp;
![MySQL](https://img.shields.io/badge/MySQL-blue?style=for-the-badge&logo=MySQL&logoColor=white&logoSize=auto) &nbsp; &nbsp; &nbsp; 
![Flask](https://img.shields.io/badge/FLASK-3.0.0-grey?style=for-the-badge&logo=flask&logoColor=white&labelColor=black) &nbsp; &nbsp; &nbsp; 
![Python](https://img.shields.io/badge/Python-3.12-orange?style=for-the-badge&logo=PYTHON&logoColor=ffdd54&labelColor=3670A0) &nbsp; &nbsp; &nbsp; 
![JavaScript](https://img.shields.io/badge/javascript-%23323330.svg?style=for-the-badge&logo=javascript&logoColor=%23F7DF1E) &nbsp; &nbsp; &nbsp; 
![HTML5](https://img.shields.io/badge/html5-%23E34F26.svg?style=for-the-badge&logo=html5&logoColor=white) &nbsp; &nbsp; &nbsp; 
![CSS3](https://img.shields.io/badge/css3-%231572B6.svg?style=for-the-badge&logo=css3&logoColor=white) &nbsp; &nbsp; &nbsp; 

<!-- table of contents-->
<details>
  <summary>Table of Contents</summary>
  <ol>
    <li>
      <a href="#About-The-Project">About The Project</a>
    </li>
    <li><a href="#How-It-Works">How It Works</a></li>
    <li><a href="#Example/Demonstration">Examples/Demonstration</a></li>
    <li><a href="#Issue">Issue</a></li>
    <li><a href="#Possible-Improvements">Possible Improvements</a></li>
    <li><a href="#license">License</a></li>
    <li><a href="#contact">Contact</a></li>
    <li><a href="#acknowledgments">Acknowledgments</a></li>
  </ol>
</details>

## About The Project
* A **full-stack website** that helps users avoid traffic jams, closed roads, etc., by sending them notifications about traffic incidents anywhere.
* The website is fully responsive and compatible with many devices. 
* Uses **Google Map API** for geocoding service and **TomTom API** for traffic incidents for the best results.
* The front end is created by Javascript, HTML, CSS, and the **React** framework. The front-end is deployed using **Cloudflare** Pages, which provide amazing **security protections** including, HTTPS, SSL/TLS encryption, DDoS and web scraping protection, prevent SQL injection and cross-site scripting, firewall protection, etc.
* The back end (server) is created using Python's **Flask framework**. It includes **security protections** such as limited CORS access to prevent attackers from sending requests to the server, rate limiting to prevent DDoS attacks, and parameterized queries technique to prevent SQL injection. The server is deployed on **Google Cloud App Engine** for fast and reliable connections.
* The server **handles all edge cases** such as users giving the wrong email, unknown locations, checking the connection to database and API services, check database storage. 
* Includes a **worker** running on **AWS Lambda Function** that sends notifications to the user when new traffic incidents appear. The function is invoked using **AWS EventBridge** every 1 minute.
* Includes one online 10 MB MySQL database.
* All come at no cost! Each cloud and online service has been carefully chosen and set up to minimize the cost due to using them ($0 paid until now).

## How It Works
* Users provide locations, time intervals, and email addresses on the website. This information is sent to the server for validation and stored in the database, and a confirmation email will be sent to the user when everything is all set. The user will start receiving emails every "time interval" if the worker program detects changes in traffic in the given locations.
* The users can also enter their email into the second form on the website to stop receiving emails!

## Example/Demonstration
https://github.com/user-attachments/assets/a4be6d38-26ff-470f-a764-a0a6ca0039c2

## Issue
* The worker program may sometimes have a delay in sending emails to users because I had set up the worker program in AWS Lambda Function to be invoked every 1 minute. This was done to prevent it from going beyond the AWS free tier. It could be fixed by having a cloud platform that allows the code to be run 24/7 continuously. 

## Possible Improvements
* Allow users to enter specific times that they want to receive notifications about traffic incidents. This is more helpful for people who only want to avoid traffic problems at a specific time of the day, like before going to work, before a trip, and when going home, etc.
* Send emails that have links that open Google Maps to show the specific roads that have traffic problems.

## License
Distributed under the MIT License. See LICENSE.txt for more information.

## Contact
William Nguyen - thangnguyen15700@gmail.com

## Acknowledgments
* AWS Lambda Function: [https://aws.amazon.com/lambda/](https://aws.amazon.com/lambda/)
* Google Cloud App Engine: [https://cloud.google.com/appengine](https://cloud.google.com/appengine)
* Database:  [https://filess.io/](https://filess.io/)
* Google Map API's geocoding service: [https://developers.google.com/maps/documentation/geocoding/overview](https://developers.google.com/maps/documentation/geocoding/overview)
* TomTom API's traffic incidents service: [https://developer.tomtom.com/traffic-api/documentation/traffic-incidents/traffic-incidents-service](https://developer.tomtom.com/traffic-api/documentation/traffic-incidents/traffic-incidents-service)
* Cloudflare Pages: [https://pages.cloudflare.com/](https://pages.cloudflare.com/)