const { withAndroidManifest } = require("@expo/config-plugins");

module.exports = function withAndroidQueries(config) {
  return withAndroidManifest(config, (config) => {
    const androidManifest = config.modResults.manifest;
    androidManifest.queries = androidManifest.queries || [];

    // Ensure we declare intent for upi:// scheme and specific UPI app packages
    androidManifest.queries.push({
      intent: [
        {
          action: [{ $: { "android:name": "android.intent.action.VIEW" } }],
          data: [{ $: { "android:scheme": "upi" } }],
        },
      ],
      package: [
        { $: { "android:name": "com.google.android.apps.nbu.paisa.user" } },
        { $: { "android:name": "com.phonepe.app" } },
        { $: { "android:name": "net.one97.paytm" } },
        { $: { "android:name": "in.org.npci.upiapp" } },
        { $: { "android:name": "com.dreamplug.androidapp" } },
      ],
    });

    return config;
  });
};
