import Link from 'next/link';
import { Menu } from 'lucide-react';

const Navbar = () => {
  return (
    <nav className="bg-primary text-foreground p-4">
      <div className="container mx-auto flex justify-between items-center">
        <div className="text-lg font-bold">Fairmind</div>
        <button className="lg:hidden p-2 rounded-md bg-secondary text-secondary-foreground">
          <Menu className="h-5 w-5" />
        </button>
        <ul className="hidden lg:flex space-x-4">
          <li><Link href="/">Home</Link></li>
          <li><Link href="/about">About</Link></li>
          <li><Link href="/contact">Contact</Link></li>
        </ul>
      </div>
    </nav>
  );
};

export default Navbar;
