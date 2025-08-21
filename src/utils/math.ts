/**
 * Mathematical utility functions for numerical calculations
 */

/**
 * Linear interpolation between two values
 */
export function lerp(a: number, b: number, t: number): number {
  return a + (b - a) * t;
}

/**
 * Clamp a value between min and max
 */
export function clamp(value: number, min: number, max: number): number {
  return Math.min(Math.max(value, min), max);
}

/**
 * Convert degrees to radians
 */
export function degToRad(degrees: number): number {
  return degrees * (Math.PI / 180);
}

/**
 * Convert radians to degrees
 */
export function radToDeg(radians: number): number {
  return radians * (180 / Math.PI);
}

/**
 * Generate linearly spaced array
 */
export function linspace(start: number, stop: number, num: number): number[] {
  if (num <= 1) return [start];
  
  const step = (stop - start) / (num - 1);
  const result: number[] = [];
  
  for (let i = 0; i < num; i++) {
    result.push(start + i * step);
  }
  
  return result;
}

/**
 * Generate logarithmically spaced array
 */
export function logspace(start: number, stop: number, num: number, base: number = 10): number[] {
  const linearValues = linspace(start, stop, num);
  return linearValues.map(val => Math.pow(base, val));
}

/**
 * Calculate mean of array
 */
export function mean(values: number[]): number {
  if (values.length === 0) return 0;
  return values.reduce((sum, val) => sum + val, 0) / values.length;
}

/**
 * Calculate standard deviation
 */
export function std(values: number[], ddof: number = 0): number {
  if (values.length <= ddof) return 0;
  
  const meanVal = mean(values);
  const squaredDiffs = values.map(val => Math.pow(val - meanVal, 2));
  const variance = squaredDiffs.reduce((sum, val) => sum + val, 0) / (values.length - ddof);
  
  return Math.sqrt(variance);
}

/**
 * Calculate median of array
 */
export function median(values: number[]): number {
  if (values.length === 0) return 0;
  
  const sorted = [...values].sort((a, b) => a - b);
  const mid = Math.floor(sorted.length / 2);
  
  return sorted.length % 2 === 0
    ? (sorted[mid - 1] + sorted[mid]) / 2
    : sorted[mid];
}

/**
 * Calculate percentile
 */
export function percentile(values: number[], p: number): number {
  if (values.length === 0) return 0;
  if (p < 0 || p > 100) throw new Error('Percentile must be between 0 and 100');
  
  const sorted = [...values].sort((a, b) => a - b);
  const index = (p / 100) * (sorted.length - 1);
  const lower = Math.floor(index);
  const upper = Math.ceil(index);
  
  if (lower === upper) return sorted[lower];
  
  const weight = index - lower;
  return sorted[lower] * (1 - weight) + sorted[upper] * weight;
}

/**
 * Calculate correlation coefficient
 */
export function corrcoef(x: number[], y: number[]): number {
  if (x.length !== y.length || x.length === 0) return 0;
  
  const meanX = mean(x);
  const meanY = mean(y);
  
  let numerator = 0;
  let denomX = 0;
  let denomY = 0;
  
  for (let i = 0; i < x.length; i++) {
    const deltaX = x[i] - meanX;
    const deltaY = y[i] - meanY;
    numerator += deltaX * deltaY;
    denomX += deltaX * deltaX;
    denomY += deltaY * deltaY;
  }
  
  const denominator = Math.sqrt(denomX * denomY);
  return denominator === 0 ? 0 : numerator / denominator;
}

/**
 * Create 2D meshgrid
 */
export function meshgrid(x: number[], y: number[]): { X: number[][], Y: number[][] } {
  const X: number[][] = [];
  const Y: number[][] = [];
  
  for (let i = 0; i < y.length; i++) {
    X.push([...x]);
    Y.push(new Array(x.length).fill(y[i]));
  }
  
  return { X, Y };
}

/**
 * Calculate 2D distance
 */
export function distance2D(x1: number, y1: number, x2: number, y2: number): number {
  return Math.sqrt(Math.pow(x2 - x1, 2) + Math.pow(y2 - y1, 2));
}

/**
 * Calculate 3D distance
 */
export function distance3D(x1: number, y1: number, z1: number, x2: number, y2: number, z2: number): number {
  return Math.sqrt(Math.pow(x2 - x1, 2) + Math.pow(y2 - y1, 2) + Math.pow(z2 - z1, 2));
}

/**
 * Normalize array to range [0, 1]
 */
export function normalize(values: number[]): number[] {
  if (values.length === 0) return [];
  
  const minVal = Math.min(...values);
  const maxVal = Math.max(...values);
  const range = maxVal - minVal;
  
  if (range === 0) return values.map(() => 0);
  
  return values.map(val => (val - minVal) / range);
}

/**
 * Scale array to specified range
 */
export function scale(values: number[], newMin: number, newMax: number): number[] {
  const normalized = normalize(values);
  const range = newMax - newMin;
  
  return normalized.map(val => newMin + val * range);
}

/**
 * Calculate moving average
 */
export function movingAverage(values: number[], windowSize: number): number[] {
  if (windowSize <= 1) return [...values];
  
  const result: number[] = [];
  
  for (let i = 0; i < values.length; i++) {
    const start = Math.max(0, i - Math.floor(windowSize / 2));
    const end = Math.min(values.length, start + windowSize);
    const window = values.slice(start, end);
    result.push(mean(window));
  }
  
  return result;
}

/**
 * Find peaks in 1D array
 */
export function findPeaks(values: number[], minHeight?: number, minDistance?: number): number[] {
  const peaks: number[] = [];
  
  for (let i = 1; i < values.length - 1; i++) {
    if (values[i] > values[i - 1] && values[i] > values[i + 1]) {
      if (minHeight === undefined || values[i] >= minHeight) {
        if (minDistance === undefined || peaks.every(peak => Math.abs(i - peak) >= minDistance)) {
          peaks.push(i);
        }
      }
    }
  }
  
  return peaks;
}

/**
 * Numerical integration using trapezoidal rule
 */
export function trapz(y: number[], x?: number[]): number {
  if (y.length < 2) return 0;
  
  const dx = x ? undefined : 1;
  let integral = 0;
  
  for (let i = 1; i < y.length; i++) {
    const deltaX = x ? x[i] - x[i - 1] : dx!;
    integral += 0.5 * (y[i] + y[i - 1]) * deltaX;
  }
  
  return integral;
}

/**
 * Numerical differentiation using finite differences
 */
export function gradient(y: number[], x?: number[]): number[] {
  if (y.length < 2) return [];
  
  const grad: number[] = [];
  
  for (let i = 0; i < y.length; i++) {
    if (i === 0) {
      // Forward difference
      const dx = x ? x[1] - x[0] : 1;
      grad.push((y[1] - y[0]) / dx);
    } else if (i === y.length - 1) {
      // Backward difference
      const dx = x ? x[i] - x[i - 1] : 1;
      grad.push((y[i] - y[i - 1]) / dx);
    } else {
      // Central difference
      const dx = x ? x[i + 1] - x[i - 1] : 2;
      grad.push((y[i + 1] - y[i - 1]) / dx);
    }
  }
  
  return grad;
}

/**
 * Solve linear system Ax = b using Gaussian elimination
 */
export function solveLinear(A: number[][], b: number[]): number[] {
  const n = A.length;
  if (n !== b.length) throw new Error('Matrix dimensions must match');
  
  // Create augmented matrix
  const augmented: number[][] = A.map((row, i) => [...row, b[i]]);
  
  // Forward elimination
  for (let i = 0; i < n; i++) {
    // Find pivot
    let maxRow = i;
    for (let k = i + 1; k < n; k++) {
      if (Math.abs(augmented[k][i]) > Math.abs(augmented[maxRow][i])) {
        maxRow = k;
      }
    }
    
    // Swap rows
    [augmented[i], augmented[maxRow]] = [augmented[maxRow], augmented[i]];
    
    // Make all rows below this one 0 in current column
    for (let k = i + 1; k < n; k++) {
      const factor = augmented[k][i] / augmented[i][i];
      for (let j = i; j <= n; j++) {
        augmented[k][j] -= factor * augmented[i][j];
      }
    }
  }
  
  // Back substitution
  const x: number[] = new Array(n);
  for (let i = n - 1; i >= 0; i--) {
    x[i] = augmented[i][n];
    for (let j = i + 1; j < n; j++) {
      x[i] -= augmented[i][j] * x[j];
    }
    x[i] /= augmented[i][i];
  }
  
  return x;
}

/**
 * Matrix multiplication
 */
export function matmul(A: number[][], B: number[][]): number[][] {
  const rowsA = A.length;
  const colsA = A[0].length;
  const colsB = B[0].length;
  
  if (colsA !== B.length) {
    throw new Error('Matrix dimensions are incompatible for multiplication');
  }
  
  const result: number[][] = Array(rowsA).fill(null).map(() => Array(colsB).fill(0));
  
  for (let i = 0; i < rowsA; i++) {
    for (let j = 0; j < colsB; j++) {
      for (let k = 0; k < colsA; k++) {
        result[i][j] += A[i][k] * B[k][j];
      }
    }
  }
  
  return result;
}

/**
 * Matrix transpose
 */
export function transpose(matrix: number[][]): number[][] {
  const rows = matrix.length;
  const cols = matrix[0].length;
  
  const result: number[][] = Array(cols).fill(null).map(() => Array(rows));
  
  for (let i = 0; i < rows; i++) {
    for (let j = 0; j < cols; j++) {
      result[j][i] = matrix[i][j];
    }
  }
  
  return result;
}

/**
 * Calculate determinant of 2x2 or 3x3 matrix
 */
export function det(matrix: number[][]): number {
  const n = matrix.length;
  
  if (n !== matrix[0].length) {
    throw new Error('Matrix must be square');
  }
  
  if (n === 2) {
    return matrix[0][0] * matrix[1][1] - matrix[0][1] * matrix[1][0];
  }
  
  if (n === 3) {
    return matrix[0][0] * (matrix[1][1] * matrix[2][2] - matrix[1][2] * matrix[2][1])
         - matrix[0][1] * (matrix[1][0] * matrix[2][2] - matrix[1][2] * matrix[2][0])
         + matrix[0][2] * (matrix[1][0] * matrix[2][1] - matrix[1][1] * matrix[2][0]);
  }
  
  throw new Error('Determinant calculation only supported for 2x2 and 3x3 matrices');
}