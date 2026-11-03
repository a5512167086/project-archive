import { useState } from "react";
import HidingMap from "./HidingMap";
import PropTypes from "prop-types";
import CustomPolygonButton from "./CustomPolygonButton";

const CustomMap = ({ customMapConfig }) => {
  const [isDrawingPolygon, setIsDrawingPolygon] = useState(false);

  const handleClickPolygonButton = () => {
    setIsDrawingPolygon(true);
  };

  return (
    <div className="custom_map_container">
      <CustomPolygonButton
        isDrawingPolygon={isDrawingPolygon}
        handleClickPolygonButton={handleClickPolygonButton}
      />
      <HidingMap
        customMapConfig={customMapConfig}
        isDrawingPolygon={isDrawingPolygon}
        setIsDrawingPolygon={setIsDrawingPolygon}
      />
    </div>
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
  customMarker: PropTypes.arrayOf(
    PropTypes.shape({
      position: PropTypes.arrayOf(PropTypes.number),
      data: PropTypes.shape({
        placeName: PropTypes.string,
        googleLocation: PropTypes.bool,
      }),
      onClickFunc: PropTypes.func,
    })
  ),
};

export default CustomMap;
