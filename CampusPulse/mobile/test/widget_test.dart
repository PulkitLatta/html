import 'package:flutter_test/flutter_test.dart';
import 'package:campuspulse/main.dart';

void main() {
  testWidgets('App starts and shows splash screen', (WidgetTester tester) async {
    // Build our app and trigger a frame.
    await tester.pumpWidget(CampusPulseApp());

    // Verify that splash screen is shown
    expect(find.text('CampusPulse'), findsOneWidget);
    expect(find.text('Athletic Performance Analytics'), findsOneWidget);
  });
}