// These are the three buttons you see
const clearBtn = document.getElementById("clear");
const undoBtn = document.getElementById("undo");
const redoBtn = document.getElementById("redo");

// The place where you draw
const result = document.querySelector('#result');
const canvas = document.querySelector('#canvas');
const ctx = canvas.getContext('2d');

let coord = { x: 0, y: 0 }; // Stores the initial position of the cursor
let prev  = { x: 0, y: 0 }; // Stores the prev position of the cursor
var drawHistory = [];
var points = [];
let isDrawing = false;

let pingTimer;


//****************************************************//
//                  Buttons Script                    //
//****************************************************//

clearBtn.addEventListener("click", function() {
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  drawHistory = [];
  points = [];
});

undoBtn.addEventListener("click", function() {
  drawHistory.splice(-1, 1);
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  drawHistory.forEach(path => {
    ctx.lineWidth = 5;
    ctx.lineCap = 'round';
    ctx.strokeStyle = 'black';
    ctx.beginPath();
    ctx.moveTo(path[0].x, path[0].y);
    for(let i = 1; i < path.length; i++) {
      ctx.lineTo(path[i].x, path[i].y);
    }
    ctx.stroke();
  });

  stopPingTimer();
  startPingTimer();
});

redoBtn.addEventListener("click", function() {
  requestPredictions();
});


//****************************************************//
//                   Canvas Script                    //
//****************************************************//

function getMousePos(event) {
  var rect = canvas.getBoundingClientRect();
  return {
    x: (event.clientX - rect.left) / (rect.right - rect.left) * canvas.width,
    y: (event.clientY - rect.top) / (rect.bottom - rect.top) * canvas.height
  };
}

function startDrawing(event) {
  isDrawing = true;
  prev = { x: coord.x, y: coord.y };
  coord = getMousePos(event);
  points = [];
  points.push(coord);
}

function stopDrawing() {
  isDrawing = false;
  drawHistory.push(points);
}

// Resizes the canvas to the available size of the window.
function resize() {
  ctx.canvas.width = window.innerWidth;
  ctx.canvas.height = window.innerHeight;
}

function draw(event) {
  if (!isDrawing) return;
  prev = { x: coord.x, y: coord.y };
  coord = getMousePos(event);
  points.push(coord);

  ctx.lineWidth = 5;
  ctx.lineCap = 'round';
  ctx.strokeStyle = 'black';
  ctx.beginPath();
  ctx.moveTo(prev.x, prev.y);
  ctx.lineTo(coord.x , coord.y);
  ctx.stroke();
}

function updateUI(updates) {
  const eqn = updates['equation'];
  const solution = updates['solution'];
  console.log(`${eqn} = ${solution}`);
  result.innerHTML = `${eqn} = ${solution}`;
}

function startPingTimer() {
  pingTimer = setTimeout(() => {
    requestPredictions();
  }, 1600);
}

function stopPingTimer() {
  clearTimeout(pingTimer);
}

window.addEventListener('load', () => {
  resize(); // Resizes the canvas once the window loads
  canvas.addEventListener('mousedown', startDrawing);
  canvas.addEventListener('mouseup', stopDrawing);
  canvas.addEventListener('mousemove', draw);
  window.addEventListener('resize', resize);

  canvas.addEventListener('mousedown', stopPingTimer);
  canvas.addEventListener('mouseup', startPingTimer);
});


//****************************************************//
//            Server Interaction Script               //
//****************************************************//

const getBase64StringFromDataURL = (dataURL) => dataURL.replace('data:', '').replace(/^.+,/, '');

function convertCanvasToBase64() {
  // Change non-opaque pixels to white
  var imgData = ctx.getImageData(0, 0, canvas.width, canvas.height);
  var data = imgData.data;
  for(var i=0; i < data.length; i+=4) {
    if(data[i+3] < 255) {
      data[i]=255;
      data[i+1]=255;
      data[i+2]=255;
      data[i+3]=255;
    }
  }
  ctx.putImageData(imgData,0,0);

  // Convert canvas to dataURL, then to Base64 string
  const dataURL = canvas.toDataURL("image/png");
  const base64 = getBase64StringFromDataURL(dataURL);
  return base64;
}

function postCanvasData(instances) {
  let xhr = new XMLHttpRequest();
  
  // Url defined here is the server endpoint. Change to http://127.0.0.1:5000/predict is testing locally
  xhr.open("POST", "https://eqnsolver.loca.lt/predict");
  xhr.setRequestHeader("Content-type", "multipart/form-data");

  // What server receives
  xhr.onload = () => {
    jsonResponse = JSON.parse(xhr.responseText);
    console.log(jsonResponse);
    updateUI(jsonResponse);
  }
  xhr.send(instances);
}

// This sends current canvas content to server endpoint for predictions
function requestPredictions() {
  const base64 = convertCanvasToBase64();
  postCanvasData(base64);
}