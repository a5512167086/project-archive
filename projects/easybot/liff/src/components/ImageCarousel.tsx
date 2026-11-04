import { useState } from "react";
import { ChevronLeft, ChevronRight } from "lucide-react";
import { Button } from "./ui/button";

interface ImageCarouselProps {
  images: { image_url: string }[];
}

export function ImageCarousel({ images }: ImageCarouselProps) {
  const [currentIndex, setCurrentIndex] = useState(0);

  const goToPrevious = () => {
    const isFirstImage = currentIndex === 0;
    const newIndex = isFirstImage ? images.length - 1 : currentIndex - 1;
    setCurrentIndex(newIndex);
  };

  const goToNext = () => {
    const isLastImage = currentIndex === images.length - 1;
    const newIndex = isLastImage ? 0 : currentIndex + 1;
    setCurrentIndex(newIndex);
  };

  if (!images || images.length === 0) {
    return (
      <div className="aspect-square w-full bg-gray-100 rounded-lg flex items-center justify-center">
        <span className="text-gray-500">No Image</span>
      </div>
    );
  }

  return (
    <div className="relative w-full aspect-square">
      <img
        src={images[currentIndex].image_url}
        alt="Product Image"
        className="w-full h-full object-cover rounded-lg"
      />
      {images.length > 1 && (
        <>
          <Button
            variant="outline"
            size="icon"
            className="absolute top-1/2 left-2 -translate-y-1/2 rounded-full h-8 w-8"
            onClick={goToPrevious}
          >
            <ChevronLeft className="h-4 w-4" />
          </Button>
          <Button
            variant="outline"
            size="icon"
            className="absolute top-1/2 right-2 -translate-y-1/2 rounded-full h-8 w-8"
            onClick={goToNext}
          >
            <ChevronRight className="h-4 w-4" />
          </Button>
        </>
      )}
      <div className="absolute bottom-2 left-1/2 -translate-x-1/2 flex space-x-2">
        {images.map((_, index) => (
          <div
            key={index}
            className={`h-2 w-2 rounded-full ${
              currentIndex === index ? "bg-black" : "bg-gray-400"
            }`}
          />
        ))}
      </div>
    </div>
  );
}