import React from 'react';
import ReactDOM from 'react-dom/client';
import './style.css';
import {MyForm, Form2} from './App';

import reportWebVitals from './reportWebVitals';



//ReactDOM.render(<MyForm/>, document.querySelector('#form'));
//ReactDOM.render(<Form2/>, document.querySelector('#unregister'));

const root1 = ReactDOM.createRoot(document.getElementById('form'));
root1.render(
  <React.StrictMode>
    <MyForm />
  </React.StrictMode>
);

const root2 = ReactDOM.createRoot(document.getElementById('unregister'));
root2.render(
  <React.StrictMode>
    <Form2 />
  </React.StrictMode>
);
