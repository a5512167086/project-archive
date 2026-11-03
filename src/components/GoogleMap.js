import { memo, useEffect } from "react";
import PropTypes from "prop-types";
import { isEmpty } from "lodash";

const GoogleMap = ({ mapData, map }) => {
  useEffect(() => {
    if (!isEmpty(mapData) && !map) {
      mapData.map.addListener("click", (event) => {
        if (event.placeId) {
          map.setView([event.latLng.lat(), event.latLng.lng()]);
          mapData.service.getDetails(
            { placeId: event.placeId },
            (place, status) => {
              if (
                status === mapData.google.maps.places.PlacesServiceStatus.OK
              ) {
                console.log(place);
              }
            }
          );
        }
      });
    }
  }, [map, mapData]);

  return <div id="map"></div>;
};

GoogleMap.propTypes = {
  mapData: PropTypes.shape({
    google: PropTypes.object,
    map: PropTypes.object,
    service: PropTypes.object,
    infowindow: PropTypes.object,
  }),
  map: PropTypes.object.isRequired,
};

export default memo(GoogleMap);
