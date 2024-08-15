using System;
using System.Collections.Generic;
using Microsoft.Maui.Controls;

namespace frontend.Controls
{
    public partial class OptimizedSlider : ContentView
    {
        public static readonly BindableProperty MinimumProperty =
            BindableProperty.Create(nameof(Minimum), typeof(double), typeof(OptimizedSlider), 0.0, propertyChanged: OnRangeChanged);

        public static readonly BindableProperty MaximumProperty =
            BindableProperty.Create(nameof(Maximum), typeof(double), typeof(OptimizedSlider), 1.0, propertyChanged: OnRangeChanged);

        public static readonly BindableProperty ValueProperty =
            BindableProperty.Create(nameof(Value), typeof(object), typeof(OptimizedSlider), 0.0, BindingMode.TwoWay, propertyChanged: OnValueChanged);

        public static readonly BindableProperty StepProperty =
            BindableProperty.Create(nameof(Step), typeof(double), typeof(OptimizedSlider), 0.1);

        public static readonly BindableProperty OptimizedValueProperty =
            BindableProperty.Create(nameof(OptimizedValue), typeof(double), typeof(OptimizedSlider), 0.0, propertyChanged: OnOptimizedValueChanged);

        public static readonly BindableProperty IsIntegerProperty =
            BindableProperty.Create(nameof(IsInteger), typeof(bool), typeof(OptimizedSlider), false, propertyChanged: OnIsIntegerChanged);

        public static readonly BindableProperty FixedValuesProperty =
            BindableProperty.Create(nameof(FixedValues), typeof(List<object>), typeof(OptimizedSlider), null, propertyChanged: OnFixedValuesChanged);

        public double Minimum
        {
            get => (double)GetValue(MinimumProperty);
            set => SetValue(MinimumProperty, value);
        }

        public double Maximum
        {
            get => (double)GetValue(MaximumProperty);
            set => SetValue(MaximumProperty, value);
        }

        public object Value
        {
            get => GetValue(ValueProperty);
            set => SetValue(ValueProperty, value);
        }

        public double Step
        {
            get => (double)GetValue(StepProperty);
            set => SetValue(StepProperty, value);
        }

        public double OptimizedValue
        {
            get => (double)GetValue(OptimizedValueProperty);
            set => SetValue(OptimizedValueProperty, value);
        }

        public bool IsInteger
        {
            get => (bool)GetValue(IsIntegerProperty);
            set => SetValue(IsIntegerProperty, value);
        }

        public List<object> FixedValues
        {
            get => (List<object>)GetValue(FixedValuesProperty);
            set => SetValue(FixedValuesProperty, value);
        }

        public OptimizedSlider()
        {
            InitializeComponent();
            MainSlider.ValueChanged += OnSliderValueChanged;
            SizeChanged += OnSizeChanged;
            Loaded += (s, e) => 
            {
                UpdateOptimizedIndicator();
                UpdateSliderBackground();
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
            slider.UpdateOptimizedLabel();
            slider.UpdateOptimizedIndicator();
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

        private void OnSliderValueChanged(object sender, ValueChangedEventArgs e)
        {
            if (FixedValues != null && FixedValues.Count > 0)
            {
                int index = (int)Math.Round(e.NewValue);
                Value = FixedValues[index];
            }
            else
            {
                double newValue = Math.Round(e.NewValue / Step) * Step;
                Value = IsInteger ? (int)Math.Round(newValue) : newValue;
            }
            UpdateValueLabel();
            UpdateOptimizedIndicator();
        }

        private void UpdateSlider()
        {
            if (FixedValues != null && FixedValues.Count > 0)
            {
                MainSlider.Minimum = 0;
                MainSlider.Maximum = FixedValues.Count - 1;
                MainSlider.Value = FixedValues.IndexOf(Value);

                MinLabel.Text = FixedValues[0].ToString();
                MaxLabel.Text = FixedValues[FixedValues.Count - 1].ToString();
            }
            else
            {
                MainSlider.Minimum = Minimum;
                MainSlider.Maximum = Maximum;
                MainSlider.Value = Convert.ToDouble(Value);

                MinLabel.Text = IsInteger ? ((int)Minimum).ToString() : Minimum.ToString("F1");
                MaxLabel.Text = IsInteger ? ((int)Maximum).ToString() : Maximum.ToString("F1");
            }

            UpdateValueLabel();
            UpdateOptimizedLabel();
            UpdateOptimizedIndicator();
        }

        private void UpdateValueLabel()
        {
            string valueText;
            if (IsInteger)
            {
                valueText = Value.ToString();
            }
            else
            {
                if (Value is float floatValue)
                {
                    valueText = floatValue.ToString("F1");
                }
                else if (Value is double doubleValue)
                {
                    valueText = doubleValue.ToString("F1");
                }
                else
                {
                    valueText = Value.ToString();
                }
            }
            ValueLabel.Text = $"Current Value: {valueText}";
        }

        private void UpdateOptimizedLabel()
        {
            if (IsInteger)
            {
                OptimizedLabel.Text = ((int)OptimizedValue).ToString();
            }
            else
            {
                OptimizedLabel.Text = OptimizedValue.ToString("F1");
            }
        }

        private void UpdateOptimizedIndicator()
        {
            if (Maximum > Minimum && MainSlider != null && OptimizedIndicator != null && OptimizedLabel != null)
            {
                double proportion = (OptimizedValue - Minimum) / (Maximum - Minimum);
                double sliderWidth = MainSlider.Width;

                OptimizedIndicator.TranslationX = proportion * sliderWidth;
                OptimizedLabel.TranslationX = proportion * sliderWidth - OptimizedLabel.Width / 2;
                OptimizedLabel.TranslationY = -OptimizedLabel.Height - 5; // Move label above the slider

                // Ensure min and max indicators are visible
                MinIndicator.IsVisible = true;
                MaxIndicator.IsVisible = true;

                // Adjust MainSlider to not overlap with indicators
                MainSlider.Margin = new Thickness(0, 0, 0, 0);
            }
        }

        private void UpdateSliderBackground()
        {
            if (MainSlider != null)
            {
                MainSlider.MinimumTrackColor = Color.FromArgb("#3366FF");
                MainSlider.MaximumTrackColor = Color.FromArgb("#CCCCCC");
            }
        }

        private void OnSizeChanged(object sender, EventArgs e)
        {
            UpdateOptimizedIndicator();
        }

        protected override void OnSizeAllocated(double width, double height)
        {
            base.OnSizeAllocated(width, height);
            UpdateOptimizedIndicator();
        }
    }
}