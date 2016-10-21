package com.byobgyn.byothermostat;

import android.content.SharedPreferences;
import android.preference.Preference;
import android.preference.PreferenceActivity;
import android.preference.PreferenceFragment;
import android.os.Bundle;
import android.preference.PreferenceManager;
import android.widget.Button;

public class SettingsActivity extends PreferenceActivity {
    public static final String SYSTEM_POWER = "system_power";
    public static final String SYSTEM_IP = "system_ip";
    public static final String TEST_MODE = "test_mode";

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        getFragmentManager().beginTransaction().replace(android.R.id.content, new AppPreferencesFragment()).commit();

//        Button button = new Button(this);
//        button.setText("Update");
//        setListFooter(button);
    }

    @Override
    public boolean isValidFragment(String fragment) {
        return true;
    }

    public static class AppPreferencesFragment extends PreferenceFragment {
        @Override
        public void onCreate(Bundle savedInstanceState) {
            super.onCreate(savedInstanceState);

            final SharedPreferences preferences = PreferenceManager.getDefaultSharedPreferences(getActivity());
            preferences.registerOnSharedPreferenceChangeListener(new SharedPreferences.OnSharedPreferenceChangeListener() {
                @Override
                public void onSharedPreferenceChanged(SharedPreferences sharedPreferences, String key) {
                    if(key.equals(SYSTEM_IP)) {
                        Preference setting = findPreference(key);
                        String value = sharedPreferences.getString(key, "");
                        if(!value.startsWith("http://")) {
                            value = "http://" + value;

                            SharedPreferences.Editor editor = sharedPreferences.edit();
                            editor.putString(SYSTEM_IP, value);
                            editor.apply();
                        }
                        setting.setSummary(value);
                    }

                    if(key.equals(SYSTEM_POWER)) {
                        boolean isChecked = sharedPreferences.getBoolean(SYSTEM_POWER, true);
                        String url = sharedPreferences.getString(SYSTEM_IP, null);
                        if(url != null) {
                            ThermoAsyncTask task = new ThermoAsyncTask();
                            String powerValue = isChecked ? "1" : "0";
                            task.execute(new ThermoTaskInput(url + "/power?value=" + powerValue, null));
                        }
                    }
                }
            });

            addPreferencesFromResource(R.xml.app_preferences);
        }
    }
}
