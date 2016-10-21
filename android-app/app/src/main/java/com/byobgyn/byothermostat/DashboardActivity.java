package com.byobgyn.byothermostat;

import android.content.Intent;
import android.content.SharedPreferences;
import android.os.Bundle;
import android.preference.PreferenceManager;
import android.support.v7.app.AppCompatActivity;
import android.view.Menu;
import android.view.MenuInflater;
import android.view.MenuItem;
import android.view.View;
import android.widget.ImageView;
import android.widget.RadioButton;
import android.widget.RadioGroup;
import android.widget.SeekBar;
import android.widget.TextView;
import android.widget.Toast;

public class DashboardActivity extends AppCompatActivity {
    private ThermoCallback callback;
    private TextView tvTemperature;
    private SeekBar tempSet;
    private RadioGroup systemMode;
    private ImageView fanStatus;
    private ImageView acStatus;
    private ImageView heatStatus;
    private String currentTemp = "--";
    private SeekBar.OnSeekBarChangeListener setTempListener;
    private RadioGroup.OnCheckedChangeListener systemModeListener;
    private ThermoReport testReport;
    private boolean testMode = false;
    private String baseUrl;

    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_dashboard);

        testReport = new ThermoReport();
        testReport.systemPower = "1";
        testReport.currentTemp = "70";
        testReport.systemThreshold = "70";
        testReport.systemMode = "0";
        testReport.fanStatus = "1";
        testReport.acStatus = "0";
        testReport.heatStatus = "1";

        tvTemperature = (TextView)findViewById(R.id.tvTemp);
        tempSet = (SeekBar)findViewById(R.id.sbSetTemp);
        systemMode = (RadioGroup)findViewById(R.id.systemMode);
        fanStatus = (ImageView)findViewById(R.id.fanStatus);
        acStatus = (ImageView)findViewById(R.id.acStatus);
        heatStatus = (ImageView)findViewById(R.id.heatStatus);

        callback = new ThermoCallback() {
            @Override
            public void onComplete(ThermoReport report) {
                if(report != null) {
                    // remove listeners
                    tempSet.setOnSeekBarChangeListener(null);
                    systemMode.setOnCheckedChangeListener(null);

                    // update UI
                    updateUi(report);

                    // replace listeners
                    tempSet.setOnSeekBarChangeListener(setTempListener);
                    systemMode.setOnCheckedChangeListener(systemModeListener);
                }
            }
        };

        // setup seek bar actions
        setTempListener = new SeekBar.OnSeekBarChangeListener() {
            @Override
            public void onProgressChanged(SeekBar seekBar, int progress, boolean fromUser) {
                tvTemperature.setText(currentTemp + " / " + progress);
            }

            @Override
            public void onStartTrackingTouch(SeekBar seekBar) { /* dont care */ }

            @Override
            public void onStopTrackingTouch(SeekBar seekBar) {
                Integer value = seekBar.getProgress();
                if(!testMode) {
                    ThermoAsyncTask task = new ThermoAsyncTask();
                    task.execute(new ThermoTaskInput(baseUrl + "/temp?value=" + value, callback));
                }
                else {
                    testReport.systemThreshold = value.toString();
                    Toast.makeText(getApplicationContext(), "Setting Temp: " + value, Toast.LENGTH_LONG).show();
                }
            }
        };

        // setup mode toggling
        systemModeListener = new RadioGroup.OnCheckedChangeListener() {
            @Override
            public void onCheckedChanged(RadioGroup group, int checkedId) {
                RadioButton btn = (RadioButton)group.findViewById(checkedId);
                if(!testMode) {
                    ThermoAsyncTask task = new ThermoAsyncTask();
                    task.execute(new ThermoTaskInput(baseUrl + "/mode?value=" + btn.getTag(), callback));
                }
                else {
                    testReport.systemMode = btn.getTag().toString();
                    Toast.makeText(getApplicationContext(), "Setting Mode: " + testReport.systemMode, Toast.LENGTH_LONG).show();
                }
            }
        };
    }

    @Override
    protected void onResume() {
        super.onResume();

        SharedPreferences preferences = PreferenceManager.getDefaultSharedPreferences(this);
        boolean systemPower = preferences.getBoolean(SettingsActivity.SYSTEM_POWER, true);
        if (systemPower) {
            baseUrl = preferences.getString(SettingsActivity.SYSTEM_IP, "");
            testMode = preferences.getBoolean(SettingsActivity.TEST_MODE, false);
            if (testMode) {
                updateUi(testReport);

                tempSet.setOnSeekBarChangeListener(setTempListener);
                systemMode.setOnCheckedChangeListener(systemModeListener);
            }
            else {
                // get the system report
                ThermoAsyncTask task = new ThermoAsyncTask();
                task.execute(new ThermoTaskInput(baseUrl, callback));
            }
        }
    }

    @Override
    public boolean onCreateOptionsMenu(Menu menu) {
        MenuInflater inflater = getMenuInflater();
        inflater.inflate(R.menu.main_menu, menu);
        return true;
    }

    @Override
    public boolean onOptionsItemSelected(MenuItem item) {
        switch (item.getItemId()) {
            case R.id.menu_refresh: {
                ThermoAsyncTask task = new ThermoAsyncTask();
                task.execute(new ThermoTaskInput(baseUrl, callback));
                return true;
            }
            case R.id.menu_options: {
                Intent intent = new Intent(this, SettingsActivity.class);
                startActivity(intent);
                return true;
            }
            default:
                return true;
        }
    }

    private void updateUi(ThermoReport report) {
        currentTemp = report.currentTemp;

        // update ui
        tvTemperature.setText(currentTemp + " / " + report.systemThreshold);
        tempSet.setProgress(Integer.parseInt(report.systemThreshold));

        RadioButton btn = (RadioButton)systemMode.findViewWithTag(report.systemMode);
        btn.setChecked(true);

        fanStatus.setVisibility(report.fanStatus.equals("true") ? View.VISIBLE : View.GONE);
        acStatus.setVisibility(report.acStatus.equals("true") ? View.VISIBLE : View.GONE);
        heatStatus.setVisibility(report.heatStatus.equals("true") ? View.VISIBLE : View.GONE);
    }
}
