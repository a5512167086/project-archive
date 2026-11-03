import React from "react";

const CustomPolygonButton = ({
  isDrawingPolygon,
  handleClickPolygonButton,
}) => {
  return (
    <button className="draw_polygon_button" onClick={handleClickPolygonButton}>
      {!isDrawingPolygon ? "Draw a Polygon" : "Drawing..."}
    </button>
  );
};

export default CustomPolygonButton;
