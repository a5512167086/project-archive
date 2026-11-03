import { Marker, Popup } from "react-leaflet";
import { customIcon } from "../config/common";
import PropTypes from "prop-types";

const CustomMarker = ({
  marker,
  map,
  onClickFunc,
  handleSetWaypoints,
  isWaypoint,
  order,
}) => {
  return (
    <Marker
      key={marker.data.placeName}
      icon={customIcon(order)}
      position={marker.position}
      eventHandlers={{
        click: () => {
          map.setView(marker.position);

          if (onClickFunc) {
            onClickFunc(marker);
          }
        },
      }}
    >
      <Popup autoPan={false}>
        <div>
          {marker.data.placeName}
          <div>
            {marker.data.googleLocation && (
              <a
                href={`https://www.google.com/maps/search/?api=1&query=${marker.position[0]}%2C${marker.position[1]}`}
                target="_blank"
                rel="noreferrer"
              >
                在Google地圖上查看
              </a>
            )}
          </div>
          <div>
            {marker.data.googleLocation && (
              <a
                href={`https://www.google.com/maps/@?api=1&map_action=pano&viewpoint=${marker.position[0]}%2C${marker.position[1]}`}
                target="_blank"
                rel="noreferrer"
              >
                Google街景服務
              </a>
            )}
          </div>
          <div>
            {marker.data.googleLocation && (
              <a
                href={`https://www.google.com/maps/dir/?api=1&destination=${marker.position[0]}%2C${marker.position[1]}`}
                target="_blank"
                rel="noreferrer"
              >
                Google導航服務
              </a>
            )}
            <span
              className="marker_waypoint_button"
              onClick={() => {
                handleSetWaypoints(marker, isWaypoint);
              }}
            >
              {isWaypoint ? "移除導航" : "加入導航"}
            </span>
          </div>
        </div>
      </Popup>
    </Marker>
  );
};

CustomMarker.propTypes = {
  marker: PropTypes.shape({
    position: PropTypes.arrayOf(PropTypes.number),
    data: PropTypes.shape({
      placeName: PropTypes.string.isRequired,
      googleLocation: PropTypes.bool.isRequired,
    }),
  }),
  map: PropTypes.object.isRequired,
  onClickFunc: PropTypes.func,
  handleSetWaypoints: PropTypes.func.isRequired,
  isWaypoint: PropTypes.bool,
  order: PropTypes.number,
};

export default CustomMarker;
