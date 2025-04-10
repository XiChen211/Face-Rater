# Face-Rater
YOLOv8 Face Detection，CNNRegression Evaluator

# Facial Beauty Scoring System

A desktop application that detects human faces in images and provides a beauty score using deep learning models.

![Application Screenshot](./images/app_screenshot.png)

## Project Overview

This application combines computer vision and deep learning to:
1. Detect human faces in photos using YOLOv8
2. Score facial attractiveness using a CNN regression model
3. Provide a user-friendly interface with PyQt5

## Technologies Used

- **Python 3.12**
- **PyQt5** - For the desktop UI
- **OpenCV** - Image processing
- **PyTorch** - Deep learning framework
- **YOLOv8** - Face detection model (via Ultralytics)
- **Hugging Face** - For model downloading

## Features

- **Intuitive UI**: Modern dark theme with clear feedback
- **Drag & Drop**: Easy image uploading through drag and drop
- **Real-time Processing**: Background thread processing with progress indication
- **Face Detection**: Automatically identifies and highlights faces in images
- **Beauty Scoring**: Returns a numerical attractiveness score based on facial features

## Project Structure

```
facial-beauty-scoring/
├── main.py                 # Application entry point
├── config.py               # Configuration and model paths
├── models.py               # Neural network model definitions
├── processing.py           # Image processing and model inference
├── ui_main_window.py       # UI implementation
├── utils.py                # Utility functions
├── requirements.txt        # Dependencies
├── beauty_cnn_model.pth    # Pre-trained beauty scoring model (needs to be downloaded)
└── images/                 # Screenshots and example images
```

## Installation


### Setup Steps

1. Clone the repository
```bash
git clone https://github.com/yourusername/facial-beauty-scoring.git
cd facial-beauty-scoring
```

2. Create and activate a virtual environment (optional but recommended)
```bash
conda create -n facial-beauty-scoring python=3.12
conda activate facial-beauty-scoring
```

3. Install dependencies
```bash
pip install -r requirements.txt
```

4. Download model files
   - YOLOv8 model will be automatically downloaded from Hugging Face on first run
   - Download the beauty CNN model file from the Baidu Cloud link:
     - Link: [https://pan.baidu.com/s/1Q1Qd97oV4A6-2yrm1m0zTA](https://pan.baidu.com/s/1Q1Qd97oV4A6-2yrm1m0zTA)
     - Extraction code: `2112`
   - Place the `beauty_cnn_model.pth` file in the project root directory

## Usage

1. Run the application
```bash
python main.py
```

2. Use the application
   - Click "Upload Image" to select an image from your computer
   - Or drag and drop an image file directly onto the application
   - The application will process the image, detect faces, and display a beauty score
   - The detected face will be highlighted with a green bounding box

![Detection Result](./images/detection_result.png)


## Development Notes

- The application uses a background thread to process images without freezing the UI
- Both models (YOLOv8 and the beauty CNN) are loaded at startup to minimize processing time
- Error handling is implemented throughout the application for a better user experience
- The interface features a modern dark theme designed for clarity and ease of use

## Limitations

- Only the first detected face in an image is processed
- Results are dependent on the quality of the input image
- The beauty score is subjective and based on the training data of the model

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgements

- YOLOv8 face detection model from [Hugging Face](https://huggingface.co/arnabdhar/YOLOv8-Face-Detection)
- Built with [PyQt5](https://riverbankcomputing.com/software/pyqt/), [OpenCV](https://opencv.org/), and [PyTorch](https://pytorch.org/)
