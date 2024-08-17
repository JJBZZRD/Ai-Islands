using System;
using System.Collections.Generic;
using Microsoft.Maui.Controls;

namespace frontend.Controls
{
    public partial class OptimizedSlider : ContentView
    {
        public static readonly BindableProperty MinimumProperty =
            BindableProperty.Create(nameof(Minimum), typeof(float), typeof(OptimizedSlider), 0f, propertyChanged: OnRangeChanged);

        public static readonly BindableProperty MaximumProperty =
            BindableProperty.Create(nameof(Maximum), typeof(float), typeof(OptimizedSlider), 1f, propertyChanged: OnRangeChanged);

        public static readonly BindableProperty ValueProperty =
            BindableProperty.Create(nameof(Value), typeof(float), typeof(OptimizedSlider), 0f, BindingMode.TwoWay, propertyChanged: OnValueChanged);

        public static readonly BindableProperty StepProperty =
            BindableProperty.Create(nameof(Step), typeof(float), typeof(OptimizedSlider), 0.1f);

        public static readonly BindableProperty OptimizedValueProperty =
            BindableProperty.Create(nameof(OptimizedValue), typeof(float), typeof(OptimizedSlider), 0f, propertyChanged: OnOptimizedValueChanged);

        public static readonly BindableProperty IsIntegerProperty =
            BindableProperty.Create(nameof(IsInteger), typeof(bool), typeof(OptimizedSlider), false, propertyChanged: OnIsIntegerChanged);

        public static readonly BindableProperty FixedValuesProperty =
            BindableProperty.Create(nameof(FixedValues), typeof(IList<float>), typeof(OptimizedSlider), null, propertyChanged: OnFixedValuesChanged);

        public static readonly BindableProperty FloatPlacesProperty =
            BindableProperty.Create(nameof(FloatPlaces), typeof(int), typeof(OptimizedSlider), 2, propertyChanged: OnFloatPlacesChanged);

        public float Minimum
        {
            get => (float)GetValue(MinimumProperty);
            set => SetValue(MinimumProperty, value);
        }

        public float Maximum
        {
            get => (float)GetValue(MaximumProperty);
            set => SetValue(MaximumProperty, value);
        }

        public float Value
        {
            get => (float)GetValue(ValueProperty);
            set => SetValue(ValueProperty, value);
        }

        public float Step
        {
            get => (float)GetValue(StepProperty);
            set => SetValue(StepProperty, value);
        }

        public float OptimizedValue
        {
            get => (float)GetValue(OptimizedValueProperty);
            set => SetValue(OptimizedValueProperty, value);
        }

        public bool IsInteger
        {
            get => (bool)GetValue(IsIntegerProperty);
            set => SetValue(IsIntegerProperty, value);
        }

        public IList<float> FixedValues
        {
            get => (IList<float>)GetValue(FixedValuesProperty);
            set => SetValue(FixedValuesProperty, value);
        }

        public int FloatPlaces
        {
            get => (int)GetValue(FloatPlacesProperty);
            set => SetValue(FloatPlacesProperty, value);
        }

        public OptimizedSlider()
        {
            InitializeComponent();
            MainSlider.ValueChanged += OnSliderValueChanged;
            SizeChanged += OnSizeChanged;
            Loaded += (s, e) => 
            {
                UpdateSlider();
                UpdateOptimizedIndicator();
            };
        }

        private static void OnRangeChanged(BindableObject bindable, object oldValue, object newValue)
        {
            var slider = (OptimizedSlider)bindable;
            slider.UpdateSlider();
        }

        private static void OnValueChanged(BindableObject bindable, object oldValue, object newValue)
        {
            var slider = (OptimizedSlider)bindable;
            slider.UpdateSlider();
        }

        private static void OnOptimizedValueChanged(BindableObject bindable, object oldValue, object newValue)
        {
            var slider = (OptimizedSlider)bindable;
            slider.UpdateOptimizedIndicator();
            slider.UpdateOptimizedLabel();
        }

        private static void OnIsIntegerChanged(BindableObject bindable, object oldValue, object newValue)
        {
            var slider = (OptimizedSlider)bindable;
            slider.UpdateSlider();
        }

        private static void OnFixedValuesChanged(BindableObject bindable, object oldValue, object newValue)
        {
            var slider = (OptimizedSlider)bindable;
            slider.UpdateSlider();
        }

        private static void OnFloatPlacesChanged(BindableObject bindable, object oldValue, object newValue)
        {
            var slider = (OptimizedSlider)bindable;
            slider.UpdateSlider();
        }

        private void UpdateSlider()
        {
            if (FixedValues != null && FixedValues.Count > 0)
            {
                MainSlider.Minimum = 0;
                MainSlider.Maximum = FixedValues.Count - 1;
                int index = FindClosestFixedValueIndex(Value);
                MainSlider.Value = index;
            }
            else
            {
                MainSlider.Minimum = Minimum;
                MainSlider.Maximum = Maximum;
                MainSlider.Value = Value;
            }

            UpdateLabels();
            UpdateValueLabel();
            UpdateOptimizedLabel();
            UpdateOptimizedIndicator();
        }

        private int FindClosestFixedValueIndex(float value)
        {
            if (FixedValues == null || FixedValues.Count == 0)
                return -1;

            return FixedValues
                .Select((v, i) => new { Value = v, Index = i })
                .OrderBy(x => Math.Abs(x.Value - value))
                .First()
                .Index;
        }

        private void UpdateLabels()
        {
            MinLabel.Text = FormatValue(Minimum);
            MaxLabel.Text = FormatValue(Maximum);
        }

        private void UpdateValueLabel()
        {
            ValueLabel.Text = $"Current Value: {FormatValue(Value)}";
        }

        private void UpdateOptimizedLabel()
        {
            OptimizedLabel.Text = FormatValue(OptimizedValue);
        }

        private void UpdateOptimizedIndicator()
        {
            if (Maximum > Minimum && MainSlider != null && OptimizedIndicator != null && OptimizedLabel != null)
            {
                float proportion = (OptimizedValue - Minimum) / (Maximum - Minimum);
                double sliderWidth = MainSlider.Width;

                OptimizedIndicator.TranslationX = proportion * sliderWidth;
                OptimizedLabel.TranslationX = proportion * sliderWidth - OptimizedLabel.Width / 2;
                OptimizedLabel.TranslationY = -OptimizedLabel.Height - 5;
            }
        }

        private void OnSliderValueChanged(object sender, ValueChangedEventArgs e)
        {
            float newValue;
            if (FixedValues != null && FixedValues.Count > 0)
            {
                int index = (int)Math.Round(e.NewValue);
                newValue = FixedValues[index];
            }
            else
            {
                newValue = (float)e.NewValue;
            }

            Value = FormatValueAsFloat(newValue);
            UpdateValueLabel();
        }

        private void OnSizeChanged(object sender, EventArgs e)
        {
            UpdateOptimizedIndicator();
        }

        private string FormatValue(float value)
        {
            return IsInteger ? value.ToString("F0") : value.ToString($"F{FloatPlaces}");
        }

        private float FormatValueAsFloat(float value)
        {
            return IsInteger ? (float)Math.Round(value) : (float)Math.Round(value, FloatPlaces);
        }
    }
}