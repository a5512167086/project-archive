import { useMapEvents } from "react-leaflet";
import PropTypes from "prop-types";

const HidingMapAction = ({
  mapData,
  isDrawingPolygon,
  currentPolygon,
  setCurrentPolygon,
  setPolygonList,
  setIsDrawingPolygon,
  setTempLine,
}) => {
  const map = useMapEvents({
    autopanstart: () => {
      mapData.map.setCenter(map.getCenter());
      mapData.map.setZoom(map.getZoom());
    },
    click: (event) => {
      // 是否在畫圖
      if (isDrawingPolygon) {
        const { lat, lng } = event.latlng;
        const newPoint = [lat, lng];

        // 當前圖形是否有節點
        if (currentPolygon.length > 0) {
          const firstPoint = currentPolygon[0];
          const distance = Math.sqrt(
            Math.pow(newPoint[0] - firstPoint[0], 2) +
              Math.pow(newPoint[1] - firstPoint[1], 2)
          );

          // 允許微小誤差
          if (distance < 0.0001) {
            // 停止繪圖
            setIsDrawingPolygon(false);
            // 將結果新增至已完成的多邊形
            setPolygonList((prev) => [...prev, currentPolygon]);
            // 重置當前多邊形
            setCurrentPolygon([]);
            setTempLine(null);
            return;
          }
        }

        // 繪製當前多邊形
        setCurrentPolygon((prev) => [...prev, newPoint]);
      }
    },
    movestart: () => {
      mapData.map.setCenter(map.getCenter());
      mapData.map.setZoom(map.getZoom());
    },
    move: () => {
      mapData.map.setCenter(map.getCenter());
      mapData.map.setZoom(map.getZoom());
    },
    moveend: () => {
      mapData.map.setCenter(map.getCenter());
      mapData.map.setZoom(map.getZoom());
    },
    dragstart: () => {
      mapData.map.setCenter(map.getCenter());
    },
    drag: () => {
      mapData.map.setCenter(map.getCenter());
    },
    dragend: () => {
      mapData.map.setCenter(map.getCenter());
    },
    zoomstart: () => {
      mapData.map.setCenter(map.getCenter());
      mapData.map.setZoom(map.getZoom());
    },
    zoom: () => {
      mapData.map.setCenter(map.getCenter());
      mapData.map.setZoom(map.getZoom());
    },
    zoomend: () => {
      mapData.map.setCenter(map.getCenter());
      mapData.map.setZoom(map.getZoom());
    },
    mousemove: (event) => {
      // 當正在繪製多邊形且已有至少一個點時，動態更新臨時線條
      if (isDrawingPolygon && currentPolygon.length > 0) {
        const { lat, lng } = event.latlng;
        const newPoint = [lat, lng];

        // 設置臨時線條的終點
        setTempLine([currentPolygon[currentPolygon.length - 1], newPoint]);
      }
    },
  });

  return null;
};

HidingMapAction.propTypes = {
  mapData: PropTypes.shape({
    google: PropTypes.object,
    map: PropTypes.object,
    service: PropTypes.object,
    infowindow: PropTypes.object,
  }),
};

export default HidingMapAction;
