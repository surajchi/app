module.exports = function (api) {
  api.cache(true);
  return {
    presets: [
      ['babel-preset-expo', { jsxImportSource: 'nativewind' }],
      'nativewind/babel',
    ],
    // Note: babel-preset-expo (SDK 52) auto-adds react-native-reanimated/plugin
    // when reanimated is installed, so it is not listed here.
  };
};
