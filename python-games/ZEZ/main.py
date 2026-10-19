"""Launch ZEZ from any working directory."""
import argparse
import os


def main():
    parser = argparse.ArgumentParser(description='ZEZ · Cloud Dash / 云端冲刺')
    parser.add_argument('--headless', action='store_true', help='Use SDL dummy video/audio; never write a save')
    parser.add_argument('--frames', type=int, default=0, help='Exit after N rendered frames')
    parser.add_argument('--scene', choices=['menu', 'run', 'pause', 'over', 'boss',
                                          'workshop', 'contracts', 'perks', 'changelog', 'maps', 'practice'], default='menu')
    parser.add_argument('--character', choices=['beige', 'pink', 'purple'], help='Runner for this session')
    parser.add_argument('--boss-kind', choices=['bee', 'storm', 'crystal'], default='bee', help='Guardian for practice')
    parser.add_argument('--seed', type=int, help='Deterministic course seed')
    parser.add_argument('--screenshot', help='Save the last 1280x720 frame as PNG')
    args = parser.parse_args()
    if args.headless:
        os.environ['SDL_VIDEODRIVER'] = 'dummy'
        os.environ['SDL_AUDIODRIVER'] = 'dummy'
        if not args.frames:
            args.frames = 1
    os.environ.setdefault('PYGAME_HIDE_SUPPORT_PROMPT', '1')
    try:
        from runner.app import App
    except ModuleNotFoundError as exc:
        if exc.name == 'pygame':
            parser.exit(1, 'Pygame is missing. Run: python3 -m pip install -r requirements.txt\n')
        raise
    App(headless=args.headless, seed=args.seed, character=args.character, boss_kind=args.boss_kind).loop(args.frames, args.screenshot, args.scene)


if __name__ == '__main__':
    main()
