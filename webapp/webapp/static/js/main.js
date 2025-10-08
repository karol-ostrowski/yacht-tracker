window.onload = function() {
    /*Loads a map centered at Zegrze lake. Forbids dragging and zooming.
    Creates markers and connects to the WebSocket.
    */
    const map = L.map("map", {
        center: [52.448922, 21.031619],
        zoom: 14.5,
        zoomControl: false,
        dragging: false,
        scrollWheelZoom: false, 
        doubleClickZoom: false,
        boxZoom: false,
        keyboard: false,
        touchZoom: false
    });

    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
        attribution: "&copy; <a href='http://www.openstreetmap.org/copyright'>OpenStreetMap</a>"
    }).addTo(map);

    const markers = create_markers(map);
    connect_websocket(markers);
};

function create_markers(map) {
    /*Generates a differently colored marker with an ID on it for each tracked yacht.*/
    const markers = new Map();
    const colors = ["blue", "red", "green", "orange", "purple", "brown"]

    for (let i = 0; i < 6; ++i) {

        const markerHTML = `
            <div class="map-marker" style="background-color: ${colors[i]};">
                <div style='transform: translateY(3px);'>
                    ${(i + 1).toString()}
                </div>
            </div>
        `;

        const new_marker_icon = L.divIcon({
            className: "map-marker",
            html: markerHTML,
            iconSize: [40, 40],
            iconAnchor: [20, 20]
        });

        const new_marker = L.marker([52.448922 - i / 1000, 21.031619], {icon: new_marker_icon})
            .addTo(map)
            .bindTooltip(`Yacht ${i + 1}`)
        markers.set(i + 1, new_marker);
    }

    return markers
}

const speed1Div = document.getElementById('speed1');
const speed2Div = document.getElementById('speed2');
const speed3Div = document.getElementById('speed3');
const speed4Div = document.getElementById('speed4');
const speed5Div = document.getElementById('speed5');
const speed6Div = document.getElementById('speed6');

let speed = 0;

function connect_websocket(markers) {
    /*Connects to the WebSocket*/
    const url = "ws://localhost:8000/ws"

    ws = new WebSocket(url)

    ws.onopen = function(event) {
        console.log('WebSocket connected');
    };
  
    ws.onmessage = function(event) {        
        try {
            const data = JSON.parse(event.data);
        
            if (data.inst_speed !== undefined) {
                console.log(data.inst_speed)
                speed = data.inst_speed.toFixed(1);
            }

            console.log(data.id)

            switch (data.id) {
                case 1:
                    speed1Div.textContent = speed;
                    break;
                case 2:
                    speed2Div.textContent = speed;
                    break;
                case 3:
                    speed3Div.textContent = speed;
                    break;
                case 4:
                    speed4Div.textContent = speed;
                    break;
                case 5:
                    speed5Div.textContent = speed;
                    break;
                case 6:
                    speed6Div.textContent = speed;
                    break;
            }

            markers.get(data.id).setLatLng([data.y, data.x]);

        } catch (error) {
            console.log("Could not parse message:", event.data);
        }
    };
  
    ws.onerror = function(error) {
        console.error('WebSocket error occured:', error);
    };
  
    ws.onclose = function() {
        console.log('WebSocket disconnected. Reconnecting in 5 seconds...');
        setTimeout(connect_websocket(markers), 5000);
    };
}