import { Text, View } from 'react-native';
import Svg, { Circle, G } from 'react-native-svg';

interface Slice {
  symbol: string;
  allocation_pct: number;
}

const PALETTE = ['#34d399', '#60a5fa', '#f59e0b', '#f472b6', '#a78bfa', '#22d3ee', '#fb7185', '#facc15'];

/** Portfolio allocation donut with legend. */
export function AllocationDonut({ positions }: { positions: Slice[] }) {
  const slices = positions
    .filter((p) => p.allocation_pct > 0)
    .sort((a, b) => b.allocation_pct - a.allocation_pct)
    .slice(0, 8);

  const total = slices.reduce((sum, s) => sum + s.allocation_pct, 0);
  if (total <= 0) return null;

  const size = 132;
  const stroke = 18;
  const r = (size - stroke) / 2;
  const c = 2 * Math.PI * r;

  let offset = 0;
  return (
    <View className="flex-row items-center">
      <Svg width={size} height={size}>
        <G rotation={-90} origin={`${size / 2}, ${size / 2}`}>
          <Circle cx={size / 2} cy={size / 2} r={r} stroke="#1e293b" strokeWidth={stroke} fill="none" />
          {slices.map((s, i) => {
            const len = (s.allocation_pct / total) * c;
            const seg = (
              <Circle
                key={s.symbol}
                cx={size / 2}
                cy={size / 2}
                r={r}
                stroke={PALETTE[i % PALETTE.length]}
                strokeWidth={stroke}
                strokeDasharray={`${len} ${c - len}`}
                strokeDashoffset={-offset}
                fill="none"
              />
            );
            offset += len;
            return seg;
          })}
        </G>
      </Svg>
      <View className="ml-4 flex-1">
        {slices.map((s, i) => (
          <View key={s.symbol} className="flex-row items-center py-0.5">
            <View
              className="mr-2 h-2.5 w-2.5 rounded-sm"
              style={{ backgroundColor: PALETTE[i % PALETTE.length] }}
            />
            <Text className="flex-1 text-sm text-slate-200" numberOfLines={1}>
              {s.symbol}
            </Text>
            <Text className="text-sm font-medium text-slate-400">
              {s.allocation_pct.toFixed(1)}%
            </Text>
          </View>
        ))}
      </View>
    </View>
  );
}
