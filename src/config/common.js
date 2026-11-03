import { Loader } from "@googlemaps/js-api-loader";
import leaflet from "leaflet";

export const customIcon = (number) =>
  leaflet.divIcon({
    className: "custom-icon",
    iconSize: [22, 45],
    iconAnchor: [10, 44],
    popupAnchor: [3, -36],
    html: number >= 0 ? `<div class="icon-number">${number + 1}</div>` : null,
  });

export const customMapConfig = {
  initMapOptions: {
    position: { lat: 23.954184118526694, lng: 120.9282365933383 },
    zoom: 17,
    southWest: [-90, -Infinity],
    northEast: [90, Infinity],
    scrollWheelZoom: true,
    inertia: false,
    zoomAnimation: false,
    maxZoom: 20,
    minZoom: 3,
    maxBoundsViscosity: 1.0,
  },
  googleMapOptions: {
    disableDefaultUI: true,
    zoomControl: false,
    mapTypeControl: false,
    scaleControl: false,
    streetViewControl: false,
    rotateControl: false,
    fullscreenControl: false,
    scrollwheel: false,
    panControl: false,
    draggable: false,
  },
  customMarker: [
    {
      position: [23.955561680761715, 120.9266165390933],
      data: {
        placeName: "Mock Place1",
        googleLocation: true,
      },
      onClickFunc: () => {
        console.log("1");
      },
    },
    {
      position: [23.95515968903214, 120.92655216607695],
      data: {
        placeName: "Mock Place2",
        googleLocation: true,
      },
      onClickFunc: () => {
        console.log("2");
      },
    },
    {
      position: [23.954247849488535, 120.92535053643827],
      data: {
        placeName: "Mock Place3",
        googleLocation: true,
      },
      onClickFunc: () => {
        console.log("3");
      },
    },
    {
      position: [23.955267540594782, 120.92865501794462],
      data: {
        placeName: "Mock Place4",
        googleLocation: true,
      },
    },
    {
      position: [23.955842195113078, 120.92636346817017],
      data: {
        placeName: "Mock Place5",
        googleLocation: true,
      },
    },
  ],
};

export const loader = new Loader({
  apiKey: process.env.REACT_APP_GOOGLE_MAPS_API_KEY,
  version: "weekly",
  libraries: ["maps", "places"],
});

export const googleMap = async (googleMapOptions) => {
  let result = { google: null, map: null, service: null, infowindow: null };

  await loader
    .load()
    .then((google) => {
      const googleMap = new google.maps.Map(
        document.getElementById("map"),
        googleMapOptions
      );
      result.google = google;
      result.map = googleMap;
      result.service = new google.maps.places.PlacesService(googleMap);
      result.infowindow = new google.maps.InfoWindow();
    })
    .catch((e) => {
      console.log(e);
      return e;
    });

  return await result;
};

export const mutipleWaypointsUrlGenerator = (waypoints) => {
  let waypointsQueryParam = "&waypoints=";

  if (waypoints.length > 1) {
    waypoints.forEach((waypoint, index) => {
      if (index !== waypoints.length - 1) {
        const currentWaypoint = `${waypoint.position[0]},${waypoint.position[1]}|`;
        waypointsQueryParam += currentWaypoint;
      }
    });
  }

  const endpointQueryParam = `${
    waypoints[waypoints.length - 1].position[0]
  }%2C${waypoints[waypoints.length - 1].position[1]}`;

  return `https://www.google.com/maps/dir/?api=1&destination=${endpointQueryParam}${waypointsQueryParam}`;
};

export const polygonConfig = { fillColor: "#AE8F00", color: "#548C00" };
