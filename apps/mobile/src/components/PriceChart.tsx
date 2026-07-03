import { View } from 'react-native';
import Svg, { Defs, LinearGradient, Path, Stop } from 'react-native-svg';

interface PriceChartProps {
  history: number[];
  forecast?: number[];
  width: number;
  height?: number;
}

const PAD = 10;

/** Lightweight area chart: historical closes + a dashed forecast overlay. */
export function PriceChart({ history, forecast = [], width, height = 180 }: PriceChartProps) {
  const values = [...history, ...forecast];
  if (values.length < 2 || width <= 0) {
    return <View style={{ width, height }} />;
  }

  const min = Math.min(...values);
  const max = Math.max(...values);
  const range = max - min || 1;
  const n = values.length;
  const stepX = width / (n - 1);

  const x = (i: number) => i * stepX;
  const y = (v: number) => PAD + (1 - (v - min) / range) * (height - 2 * PAD);

  const histPath = history
    .map((v, i) => `${i === 0 ? 'M' : 'L'} ${x(i).toFixed(1)} ${y(v).toFixed(1)}`)
    .join(' ');

  const lastHistIndex = history.length - 1;
  const areaPath =
    `${histPath} L ${x(lastHistIndex).toFixed(1)} ${height} L 0 ${height} Z`;

  // Connect the forecast to the last real point so the line is continuous.
  const lastHist = history[lastHistIndex];
  const forecastSeries =
    forecast.length && lastHist !== undefined ? [lastHist, ...forecast] : [];
  const forecastPath = forecastSeries
    .map((v, i) => {
      const idx = lastHistIndex + i;
      return `${i === 0 ? 'M' : 'L'} ${x(idx).toFixed(1)} ${y(v).toFixed(1)}`;
    })
    .join(' ');

  return (
    <Svg width={width} height={height}>
      <Defs>
        <LinearGradient id="area" x1="0" y1="0" x2="0" y2="1">
          <Stop offset="0" stopColor="#34d399" stopOpacity={0.28} />
          <Stop offset="1" stopColor="#34d399" stopOpacity={0} />
        </LinearGradient>
      </Defs>
      <Path d={areaPath} fill="url(#area)" />
      <Path d={histPath} stroke="#34d399" strokeWidth={2} fill="none" />
      {forecastPath ? (
        <Path
          d={forecastPath}
          stroke="#fbbf24"
          strokeWidth={2}
          strokeDasharray="5 4"
          fill="none"
        />
      ) : null}
    </Svg>
  );
}
