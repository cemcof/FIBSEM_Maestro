from fibsem_maestro.GUI.image_label import ImageLabel


class ImageLabelManager:
    def __init__(self):
        self._image_labels = []

    def update_image(self, image):
        for image_label in self._image_labels:
            image_label.setImage(image)

    def add_image(self, image_label: ImageLabel):
        self._image_labels.append(image_label)
        for image_label_connected in self._image_labels[:-1]:
            # both directions connection
            image_label_connected.repaint_events.append(image_label.update_pan_zoom)
            image_label.repaint_events.append(image_label_connected.update_pan_zoom)

    def clear(self):
        self._image_labels.clear()

class ImageLabelManagers:
    sem_manager = ImageLabelManager()