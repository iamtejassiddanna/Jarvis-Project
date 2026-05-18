import math
import numpy as np

def test_advanced_math():
    print("--- Using Python's built-in math library ---")
    
    # Trigonometry
    angle_rad = math.radians(45)
    print(f"Sine of 45 degrees: {math.sin(angle_rad):.4f}")
    
    # Logarithms
    print(f"Log base 10 of 1000: {math.log10(1000)}")
    
    # Constants
    print(f"Value of Pi: {math.pi}")
    
    print("\n--- Using Numpy for advanced operations ---")
    
    # Matrix operations
    matrix_a = np.array([[1, 2], [3, 4]])
    matrix_b = np.array([[5, 6], [7, 8]])
    
    print("Matrix Multiplication:")
    print(np.dot(matrix_a, matrix_b))
    
    # Statistical operations
    data = np.array([15, 22, 35, 41, 55, 62])
    print(f"Mean of data: {np.mean(data)}")
    print(f"Standard deviation: {np.std(data):.4f}")
    
    # Solving linear equations (e.g., 3x + 2y = 7,  x - y = 8)
    coeffs = np.array([[3, 2], [1, -1]])
    constants = np.array([7, 8])
    solution = np.linalg.solve(coeffs, constants)
    print(f"Solution for linear equation (x, y): {solution}")

if __name__ == "__main__":
    test_advanced_math()
