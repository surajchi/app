import { Text, View } from 'react-native';
import Svg, { Circle, Path } from 'react-native-svg';

import type { SentimentIndex } from '@finpulse/types';

function polarToCartesian(cx: number, cy: number, radius: number, angle: number) {
  const radians = ((angle - 180) * Math.PI) / 180;
  return {
    x: cx + radius * Math.cos(radians),
    y: cy + radius * Math.sin(radians),
  };
}

function arcPath(cx: number, cy: number, radius: number, startAngle: number, endAngle: number) {
  const start = polarToCartesian(cx, cy, radius, endAngle);
  const end = polarToCartesian(cx, cy, radius, startAngle);
  const largeArcFlag = endAngle - startAngle <= 180 ? '0' : '1';

  return `M ${start.x} ${start.y} A ${radius} ${radius} 0 ${largeArcFlag} 0 ${end.x} ${end.y}`;
}

function scoreColor(score: number) {
  if (score < 25) return '#dc2626';
  if (score < 45) return '#f97316';
  if (score < 55) return '#64748b';
  if (score < 75) return '#16a34a';
  return '#059669';
}

export function SentimentGauge({ index }: { index: SentimentIndex }) {
  const score = Math.max(0, Math.min(100, index.score));
  const angle = (score / 100) * 180;
  const marker = polarToCartesian(60, 60, 42, angle);
  const color = scoreColor(score);
  const total = index.advancers + index.decliners;
  const breadth =
    total > 0 ? `${index.advancers}/${total} advancing` : 'Breadth neutral';

  return (
    <View className="mt-3 rounded-lg border border-slate-800 bg-slate-950 px-3 py-3">
      <View className="flex-row items-center justify-between">
        <View>
          <Text className="text-xs font-medium uppercase text-slate-500">Fear &amp; Greed</Text>
          <Text className="mt-0.5 text-lg font-bold text-slate-50">{index.label}</Text>
        </View>
        <Text style={{ color }} className="text-3xl font-bold">
          {score}
        </Text>
      </View>

      <View className="mt-2 items-center">
        <Svg width={140} height={72} viewBox="0 0 120 72">
          <Path
            d={arcPath(60, 60, 42, 0, 180)}
            stroke="#1e293b"
            strokeWidth={12}
            strokeLinecap="round"
            fill="none"
          />
          <Path
            d={arcPath(60, 60, 42, 0, angle)}
            stroke={color}
            strokeWidth={12}
            strokeLinecap="round"
            fill="none"
          />
          <Circle cx={marker.x} cy={marker.y} r={5} fill="#ffffff" stroke={color} strokeWidth={3} />
        </Svg>
      </View>

      <View className="mt-1 flex-row justify-between">
        <Text className="text-xs text-slate-500">Fear</Text>
        <Text className="text-xs font-medium text-slate-400">{breadth}</Text>
        <Text className="text-xs text-slate-500">Greed</Text>
      </View>
    </View>
  );
}
