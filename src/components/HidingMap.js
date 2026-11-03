import { useEffect, useState } from "react";
import { MapContainer, Polygon, Polyline } from "react-leaflet";
import PropTypes from "prop-types";
import GoogleMap from "./GoogleMap";
import HidingMapAction from "./HidingMapAction";
import {
  googleMap,
  mutipleWaypointsUrlGenerator,
  polygonConfig,
} from "../config/common";
import CustomMarker from "./CustomMarker";
import { FullscreenControl } from "react-leaflet-fullscreen";
import "react-leaflet-fullscreen/styles.css";

const HidingMap = ({
  customMapConfig,
  isDrawingPolygon,
  setIsDrawingPolygon,
}) => {
  const [map, setMap] = useState(null);
  const [mapData, setMapData] = useState();
  const [waypoints, setWaypoints] = useState([]);
  const [polygonList, setPolygonList] = useState([]);
  const [currentPolygon, setCurrentPolygon] = useState([]);
  const [tempLine, setTempLine] = useState(null); // 用於保存臨時線條

  const handleSetWaypoints = (newWaypoint, isWaypoint) => {
    if (isWaypoint) {
      setWaypoints((currentWaypoints) =>
        currentWaypoints.filter(
          (waypoint) => waypoint.data.placeName !== newWaypoint.data.placeName
        )
      );
    } else {
      setWaypoints([...waypoints, newWaypoint]);
    }
  };

  const handleResetWaypoints = () => {
    setWaypoints([]);
  };

  useEffect(() => {
    async function getData() {
      const googleMapOptions = {
        center: {
          lat: customMapConfig.initMapOptions.position.lat,
          lng: customMapConfig.initMapOptions.position.lng,
        },
        zoom: customMapConfig.initMapOptions.zoom,
        ...customMapConfig.googleMapOptions,
      };

      const fetchedData = await googleMap(googleMapOptions);
      setMapData(fetchedData);
    }

    getData();
  }, [customMapConfig]);

  return (
    <MapContainer
      id="hidingMap"
      center={[
        customMapConfig.initMapOptions.position.lat,
        customMapConfig.initMapOptions.position.lng,
      ]}
      zoom={customMapConfig.initMapOptions.zoom}
      scrollWheelZoom={customMapConfig.initMapOptions.scrollWheelZoom}
      inertia={customMapConfig.initMapOptions.inertia}
      zoomAnimation={customMapConfig.initMapOptions.zoomAnimation}
      maxZoom={customMapConfig.initMapOptions.maxZoom}
      minZoom={customMapConfig.initMapOptions.minZoom}
      maxBounds={[
        customMapConfig.initMapOptions.southWest,
        customMapConfig.initMapOptions.northEast,
      ]}
      maxBoundsViscosity={customMapConfig.initMapOptions.maxBoundsViscosity}
      ref={setMap}
    >
      <FullscreenControl />
      {mapData && (
        <HidingMapAction
          mapData={mapData}
          isDrawingPolygon={isDrawingPolygon}
          currentPolygon={currentPolygon}
          setCurrentPolygon={setCurrentPolygon}
          setPolygonList={setPolygonList}
          setIsDrawingPolygon={setIsDrawingPolygon}
          setTempLine={setTempLine} // 傳遞臨時線條的狀態設置函數
        />
      )}
      {customMapConfig.customMarker.map((marker) => {
        return (
          map && (
            <CustomMarker
              key={marker.data.placeName}
              marker={marker}
              map={map}
              isWaypoint={waypoints.find(
                (waypoint) => waypoint.data.placeName === marker.data.placeName
              )}
              order={waypoints.findIndex(
                (waypoint) => waypoint.data.placeName === marker.data.placeName
              )}
              onClickFunc={marker.onClickFunc}
              handleSetWaypoints={handleSetWaypoints}
            />
          )
        );
      })}
      {map && <GoogleMap mapData={mapData || {}} map={map} />}
      {waypoints.length !== 0 && (
        <div className="mutiple_waypoints_buttonBox">
          <button
            className="mutiple_waypoints_button"
            onClick={() => {
              window.open(
                mutipleWaypointsUrlGenerator(waypoints),
                "_blank",
                "noopener,noreferrer"
              );
            }}
          >
            多點導航 - {waypoints.length}
          </button>
          <button
            className="mutiple_waypoints_button"
            onClick={handleResetWaypoints}
          >
            重設導航點
          </button>
        </div>
      )}
      <Polygon pathOptions={polygonConfig} positions={polygonList} />
      {/* 當前圖形 */}
      <Polyline pathOptions={polygonConfig} positions={currentPolygon} />
      {tempLine && (
        <Polyline pathOptions={polygonConfig} positions={tempLine} />
      )}
    </MapContainer>
  );
};

HidingMap.propTypes = {
  customMapConfig: PropTypes.shape({
    initMapOptions: PropTypes.shape({
      position: PropTypes.shape({
        lat: PropTypes.number.isRequired,
        lng: PropTypes.number.isRequired,
      }),
      zoom: PropTypes.number.isRequired,
      southWest: PropTypes.arrayOf(PropTypes.number),
      northEast: PropTypes.arrayOf(PropTypes.number),
      scrollWheelZoom: PropTypes.bool.isRequired,
      inertia: PropTypes.bool.isRequired,
      zoomAnimation: PropTypes.bool.isRequired,
      maxZoom: PropTypes.number.isRequired,
      minZoom: PropTypes.number.isRequired,
      maxBoundsViscosity: PropTypes.number.isRequired,
    }),
    googleMapOptions: PropTypes.shape({
      disableDefaultUI: PropTypes.bool.isRequired,
      zoomControl: PropTypes.bool.isRequired,
      mapTypeControl: PropTypes.bool.isRequired,
      scaleControl: PropTypes.bool.isRequired,
      streetViewControl: PropTypes.bool.isRequired,
      rotateControl: PropTypes.bool.isRequired,
      fullscreenControl: PropTypes.bool.isRequired,
      scrollwheel: PropTypes.bool.isRequired,
      panControl: PropTypes.bool.isRequired,
      draggable: PropTypes.bool.isRequired,
    }),
  }),
};

export default HidingMap;
