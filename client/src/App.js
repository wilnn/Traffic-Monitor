import React from 'react';
import './style.css';

// the first form for location details, time interval, email address
export const MyForm = () => {
    // Use useState for each input field
    const [City, setCity] = React.useState('');
    const [State, setState] = React.useState('');
    const [Country, setCountry] = React.useState('');
    const [timeInterval, settimeInterval] = React.useState('');
    const [email, setEmail] = React.useState('');
  
    // Event handler for the first input field
    const handleInputChange1 = (event) => {
      // Remove spaces from the input value
      // var sanitizedValue = event.target.value.replace(/\s/g, '');
      setCity(event.target.value);
    };
    const handleInputChange2 = (event) => {
      // Remove spaces from the input value
      // var sanitizedValue = event.target.value.replace(/\s/g, '');
      setState(event.target.value);
    };
    const handleInputChange3 = (event) => {
      // Remove spaces from the input value
      // var sanitizedValue = event.target.value.replace(/\s/g, '');
      setCountry(event.target.value);
    };
  
    // Event handler for the second input field
    const handleInputChange4 = (event) => {
      settimeInterval(event.target.value);
    };
  
    const handleInputChange5 = (event) => {
      //the email input type will handle the input value. No need to sanitized the value.
      setEmail(event.target.value);
    };
  
    // Submit handler
    const handleSubmit = (event) => {
      //cancel the default submit action of the form, if the page is reloading.
      //fixed the error of console.log not showing messege due to auto page reloading
      event.preventDefault();

      // regular expression to for validating email format
      var regex = /^[a-zA-Z0-9.!#$%&'*+/=?^_`{|}~-]+@[a-zA-Z0-9-]+(?:\.[a-zA-Z0-9-]+)*$/;
      if (!email.match(regex)) {
        alert("Invalid email format.");
        return
      }

      var loading = document.getElementById('loading');
      var display = document.getElementById('display');
      // add spinning circle to the webpage
      loading.innerHTML = '<span class="loading heroLoading"></span>';

      //'<span class="loading heroLoading"></span>' will automatically disappear when reload since 
      //it is written inside that tag in the DOM not inside the actual html file

      // Send data to Flask backend
      fetch('https://traffic-433100.ue.r.appspot.com/data', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ city: City, state: State, country: Country, time: timeInterval, clientEmail : email.toLowerCase() }),
      })
        .then(response => response.json())
        .then(result => {
          console.log(result);

          // Handle the response from the Flask backend (handle error message and success message from the backend)
          if (result['value'] === 'ERROR2') {
            loading.innerHTML = '';
            display.innerHTML = '<p style="color:red;">ERROR. Can not find the provided city/state/country. Please check your input.</p>';
            } else if((result['value']) === 'ERROR1') {
            loading.innerHTML = '';
            display.innerHTML = '<p style="color:red;">ERROR. Can not verify your email. Please check.</p>';
          } else if (result['value'] === 'ERROR0') {
            loading.innerHTML = '';
            display.innerHTML = '<p style="color:red;">ERROR. Failed to connect to the database.</p>';
          } else if (result['value'] === 'ERROR3') {
            loading.innerHTML = '';
            display.innerHTML = '<p style="color:red;">Error. Can not make a request to the traffic incidents API.<br> The location you want to track need to be at most 10,000 kilometer square. try narrowing down the location.</p>';
          } else if (result['value'] === 'ok') {
            loading.innerHTML = '';
            display.innerHTML = '<p style="color:green;">You are all set!</p>';
          }  else if (('error' in result) && result['error'] === 'ratelimit exceeded') {
            loading.innerHTML = '';
            display.innerHTML = '<p style="color:red;">Too many requests. Try again later.</p>';
          } else if (result['value'] === 'ERROR4') {
            loading.innerHTML = '';
            display.innerHTML = '<p style="color:red;">The database is full! Please check back later.</p>';
          }
        })
        // catch the error when fail to send POST request to the server
        .catch(error => {
          console.error('Error:', error);
          
        });
    };
    return (
      <>
        <form onSubmit={handleSubmit}>
           <label for ="City"><p class = "heroSubText color">City or region:</p></label>
            <input type="text" value ={City} onChange={handleInputChange1} name="City" id = "City" class="inputField" maxlength="9999" required/>
            <label for ="State"><p class = "inputText color">State, or the region that includes the above region (optional):</p></label>
            <input type="text" value ={State} onChange={handleInputChange2} name="State" id = "State" class="inputField" maxlength="9999"/>
            <label for ="Country"><p class = "inputText color">Country:</p></label>
            <input type="text" value ={Country} onChange={handleInputChange3} name="Country" id = "Country" class="inputField" maxlength="9999" required/>
            <label for="timeInterval"><p class = "inputText color">Time interval (minutes):</p><p  class = "inputSubText color">The city's traffic will be checked after every this amount of time. Minimum is 10 mins.</p></label>
            <input type="number" value={timeInterval} onChange={handleInputChange4} id="timeInterval" name="timeInterval" min="10" max = "999999"step="1" placeholder="10-999999" required class="inputField2"/>
            <label for ="email"><p class = "inputText color">Email:</p></label>
            <input type = "email" value={email} onChange={handleInputChange5} id="email" name="email" required class="inputField"/><br/>
            <input type = "submit" value = "START!" class = "button color"/>
        </form>
      </>
    );
  };

export const Form2 = () => {
    const [email, setEmail] = React.useState('');
    const handleInputChange = (event) => {
      //the email input type will handle the input value. No need to sanitized the value.
      setEmail(event.target.value);
    };
  
    const handleSubmit = (event) => {
      event.preventDefault();
      console.log(email)
      var display = document.getElementById('display');
      fetch('https://traffic-433100.ue.r.appspot.com/unregister', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({clientEmail: email}),
      })
        .then(response => response.json())
        .then(result => {
          if (result['value'] === "Email does not exist in the database. Please check the entered email."){
            display.innerHTML = '<p style="color:red;">Email does not exist in the database. Please check the entered email.</p>';
          } else if (result['value'] === 'ERROR0') {
            display.innerHTML = '<p style="color:red;">Failed to connect to the database.</p>';
          } else if (('error' in result) && result['error'] === 'ratelimit exceeded') {
            display.innerHTML = '<p style="color:red;">Too many requests. Try again later.</p>';
          } else {
            display.innerHTML = '<p style="color:green;">Unregisted successfully</p>';
          }
        }
      )
      .catch(error => {
        console.error('Error:', error);
      });
    }
    return (
      <form onSubmit={handleSubmit}>
      <div class="unregister">
        <div class="unregisterItem"><label for ="email"><span class="unretext">Want to stop receiving emails? Enter your email to unregistser:</span></label></div>
        <div class="unregisterItem"><input type = "email" value={email} onChange={handleInputChange} id="email" name="email" required class="inputField"/></div>
        <div class="unregisterItem"><input type = "submit" value = "Submit" class = "button color" style={{margin:'0'}}/></div>
        </div>
      </form>
    )
  }

//export default {MyForm, Form2};