import { Pressable, ScrollView, Text, View } from 'react-native';

export interface Segment {
  label: string;
  value: string;
}

interface Props {
  options: Segment[];
  value: string;
  onChange: (value: string) => void;
  scroll?: boolean;
}

/** shadcn-style segmented tabs. Set `scroll` for long option lists (chips). */
export function SegmentedControl({ options, value, onChange, scroll = false }: Props) {
  const items = options.map((o) => (
    <Pressable
      key={o.value}
      onPress={() => onChange(o.value)}
      className={`mr-1 items-center rounded-lg px-3 py-1.5 ${
        value === o.value ? 'bg-slate-100' : 'active:bg-slate-800'
      } ${scroll ? '' : 'flex-1'}`}
    >
      <Text
        className={`text-xs font-semibold ${
          value === o.value ? 'text-slate-900' : 'text-slate-400'
        }`}
      >
        {o.label}
      </Text>
    </Pressable>
  ));

  if (scroll) {
    return (
      <ScrollView
        horizontal
        showsHorizontalScrollIndicator={false}
        className="rounded-xl border border-slate-800 bg-slate-900 p-1"
      >
        {items}
      </ScrollView>
    );
  }
  return (
    <View className="flex-row rounded-xl border border-slate-800 bg-slate-900 p-1">{items}</View>
  );
}
